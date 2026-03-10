from __future__ import annotations
from dataclasses import dataclass, field
from classiq import (
    create_model,
    synthesize_async,
    Preferences,
    set_quantum_program_execution_preferences,
    ExecutionPreferences,
    Constraints,
)
from hardwares_prefs import execution_preferences_wrapper
from reporting import *
import asyncio
import csv
import os
from pathlib import Path
import pandas as pd
import datetime

TypeResult = dict
RESULT_TIMEOUT = {"score": float("nan")}


@dataclass(frozen=True)
class BenchmarkExample:
    name: str
    num_qubits: int

    # user supplies "unrolled" callables
    get_main: callable  # (num_qubits) -> main
    execute: callable  # async (num_qubits, qprog, execution_prefs) -> results
    score: callable  # (num_qubits, results) -> TypeResult
    constraints: object = None  # constraints for synthesis

    # materialized
    main: object = None
    executor: object = None  # async (qprog, execution_prefs) -> results
    scorer: object = None  # (results) -> TypeResult

    def __post_init__(self):
        object.__setattr__(self, "main", self.get_main(self.num_qubits))

        async def executor(qprog):
            return await self.execute(self.num_qubits, qprog)

        async def scorer(job):
            return await self.score(self.num_qubits, job)

        object.__setattr__(self, "executor", executor)
        object.__setattr__(self, "scorer", scorer)


@dataclass
class HardwareRunner:
    exec_sem: object  # asyncio.Semaphore(3)
    max_timeout: int  # seconds
    backend_service_provider: str
    backend_name: str
    num_shots: int
    backend_kwargs: dict = field(default_factory=dict)

    def _get_syn_prefs(self):
        if self.backend_service_provider == "Classiq":
            return Preferences()
        else:
            return Preferences(
                backend_service_provider=self.backend_service_provider,
                backend_name=self.backend_name,
            )

    def _get_exe_prefs(self):
        return ExecutionPreferences(
            num_shots=self.num_shots,
            backend_preferences=execution_preferences_wrapper(
                self.backend_service_provider,
                self.backend_name,
                **self.backend_kwargs,
            ),
        )

    async def build(self, example: BenchmarkExample):
        constraints = (
            example.constraints if example.constraints is not None else Constraints()
        )
        qmod = create_model(
            example.main, preferences=self._get_syn_prefs(), constraints=constraints
        )
        qprog = await synthesize_async(qmod)
        qprog = set_quantum_program_execution_preferences(qprog, self._get_exe_prefs())
        return qprog

    async def submit_to_backend(self, example: BenchmarkExample) -> TypeResult:
        qprog = await self.build(example)

        await self.exec_sem.acquire()
        try:
            job_id = await example.executor(qprog)
        finally:
            self.exec_sem.release()

        return job_id

    async def get_backend_score(
        self, example: BenchmarkExample, job_id: str
    ) -> TypeResult:
        return await example.scorer(job_id)

    async def _run_with_timeout(
        self, example: BenchmarkExample, job_id: str
    ) -> TypeResult:
        try:
            return await asyncio.wait_for(
                self.get_backend_score(example, job_id), timeout=self.max_timeout
            )
        except asyncio.TimeoutError:
            return RESULT_TIMEOUT

    async def run(self, example: BenchmarkExample) -> TypeResult:
        """
        Full run of a benchmark example. When running several examples asynchronously use
        the class ResultCollector instead, which separates the submission and scoring.
        """
        result = {
            "example": example.name,
            "num_qubits": example.num_qubits,
            "backend_service_provider": self.backend_service_provider,
            "backend_name": self.backend_name,
            "submitted_timestamp": datetime.datetime.now(),
        }
        job_id = await self.submit_to_backend(example)
        result["status"] = "SUBMITTED"
        result["job_id"] = job_id
        scores = await self._run_with_timeout(example, job_id)
        result["status"] = "COMPLETED"
        result_time = datetime.datetime.now()
        result.update(scores)
        result.update({"timestamp": result_time})
        return result


# Constants for ResultCollector
RESULT_TIMEOUT = {"score": float("nan")}
FIELDNAMES = [
    "Example",
    "Qubits",
    "Provider",
    "Backend Name",
    "Num Shots",
    "Status",
    "Job ID",
    "Submitted Time",
    "Completed Time",
    "Score",
]


# Utility functions for ResultCollector
def dt_to_str(dt):
    if isinstance(dt, datetime.datetime):
        return dt.isoformat(timespec="seconds")
    return "" if dt is None else str(dt)


def str_to_dt(s: str):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


def result_key(result: dict):
    return (
        result.get("example"),
        result.get("num_qubits"),
        result.get("backend_service_provider"),
        result.get("backend_name"),
        result.get("num_shots"),
    )


def make_key(example, runner):
    return (
        getattr(example, "name", "UNKNOWN"),
        int(getattr(example, "num_qubits", -1)),
        runner.backend_service_provider,
        runner.backend_name,
        int(runner.num_shots),
    )


def find_index_by_key(results: list[dict], key: tuple):
    for i, r in enumerate(results):
        if result_key(r) == key:
            return i
    return None


def result_to_row(r: dict) -> dict:
    return {
        "Example": r.get("example", ""),
        "Qubits": r.get("num_qubits", ""),
        "Provider": r.get("backend_service_provider", ""),
        "Backend Name": r.get("backend_name", ""),
        "Num Shots": r.get("num_shots", ""),
        "Status": r.get("status", ""),
        "Job ID": r.get("job_id", ""),
        "Submitted Time": dt_to_str(r.get("submitted_timestamp")),
        "Completed Time": dt_to_str(r.get("timestamp")),
        "Score": r.get("score", ""),
    }


def row_to_result(row: dict) -> dict:
    def to_int(x):
        try:
            return int(float(x))
        except Exception:
            return None

    def to_float(x):
        try:
            return float(x)
        except Exception:
            return None

    return {
        "example": row.get("Example", ""),
        "num_qubits": to_int(row.get("Qubits", "")),
        "backend_service_provider": row.get("Provider", ""),
        "backend_name": row.get("Backend Name", ""),
        "num_shots": to_int(row.get("Num Shots", "")),
        "status": row.get("Status", ""),
        "job_id": row.get("Job ID", ""),
        "submitted_timestamp": str_to_dt(row.get("Submitted Time", "")),
        "timestamp": str_to_dt(row.get("Completed Time", "")),
        "score": to_float(row.get("Score", "")),
    }


def read_results_csv(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [row_to_result(row) for row in reader]


def write_results_csv_atomic(path: str, results: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        for r in results:
            w.writerow(result_to_row(r))
    os.replace(tmp, path)


def make_df_for_example_qubits(
    results: list[dict], example_name: str, num_qubits: int
) -> pd.DataFrame:
    rows = []
    for r in results:
        if r.get("example") != example_name:
            continue
        if r.get("num_qubits") != num_qubits:
            continue
        if r.get("status") not in {"COMPLETED", "TIMEOUT", "ERROR"}:
            continue

        submitted = r.get("submitted_timestamp")
        completed = r.get("timestamp")

        elapsed_min = None
        if isinstance(submitted, datetime.datetime) and isinstance(
            completed, datetime.datetime
        ):
            elapsed_sec = (completed - submitted).total_seconds()
            elapsed_min = elapsed_sec / 60.0

        rows.append(
            {
                "Provider": r.get("backend_service_provider", ""),
                "Backend Name": r.get("backend_name", ""),
                "Score": r.get("score", float("nan")),
                "Time Elapsed (min)": elapsed_min,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # --- formatting rules ---
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce").round(4)

    df["Time Elapsed (min)"] = pd.to_numeric(
        df["Time Elapsed (min)"], errors="coerce"
    ).round(1)

    df = df.sort_values(["Provider", "Backend Name"]).reset_index(drop=True)
    return df


def section_name(example_name: str, num_qubits: int) -> str:
    return f"{example_name.lower().replace(' ', '_')}_q{num_qubits}"


def section_title(example_name: str, num_qubits: int) -> str:
    return f"{example_name} - {num_qubits} qubits"


class ResultCollector:
    def __init__(
        self,
        filename: str,
        reset_file: bool = False,
        report_root: str = "../report",
        build_each_time: bool = False,
    ):
        self.filename = filename
        self.lock = asyncio.Lock()
        self.report_root = report_root
        self.build_each_time = build_each_time

        if reset_file:
            self.results = []
            write_results_csv_atomic(self.filename, self.results)
        else:
            self.results = read_results_csv(self.filename)

    async def _upsert_and_write(self, key: tuple, patch: dict) -> dict:
        """
        Must be called under the lock.
        """
        idx = find_index_by_key(self.results, key)
        if idx is None:
            self.results.append(patch.copy())
            idx = len(self.results) - 1
        else:
            self.results[idx].update(patch)

        write_results_csv_atomic(self.filename, self.results)
        return dict(self.results[idx])

    async def run_hardware(self, runner, example) -> dict:
        key = make_key(example, runner)

        # 1) Decide what to do (quick, under lock)
        async with self.lock:
            idx = find_index_by_key(self.results, key)
            existing = self.results[idx] if idx is not None else None

            if existing and existing.get("status") == "COMPLETED":
                return dict(existing)

            if (
                existing
                and existing.get("status") == "SUBMITTED"
                and existing.get("job_id")
            ):
                job_id = existing["job_id"]
                need_submit = False
            else:
                job_id = None
                need_submit = True

        # 2) Submit if needed (network, OUTSIDE lock)
        if need_submit:
            job_id = await runner.submit_to_backend(example)
            submitted_ts = datetime.datetime.now()
            print(
                f"{submitted_ts}: Submit {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name}"
            )

            async with self.lock:
                await self._upsert_and_write(
                    key,
                    {
                        "example": example.name,
                        "num_qubits": example.num_qubits,
                        "backend_service_provider": runner.backend_service_provider,
                        "backend_name": runner.backend_name,
                        "num_shots": runner.num_shots,
                        "status": "SUBMITTED",
                        "job_id": job_id,
                        "submitted_timestamp": submitted_ts,
                    },
                )

        # 3) Score (network, OUTSIDE lock)
        try:
            scores = await asyncio.wait_for(
                runner.get_backend_score(example, job_id),
                timeout=runner.max_timeout,
            )
            status = "COMPLETED"
        except asyncio.TimeoutError:
            scores = RESULT_TIMEOUT
            status = "TIMEOUT"

        completed_ts = datetime.datetime.now()
        print(
            f"{completed_ts}: Completed {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name} --> Score {scores}"
        )

        # 4) Finalize + write (quick, under lock)
        async with self.lock:
            final_result = await self._upsert_and_write(
                key,
                {
                    "status": status,
                    "timestamp": completed_ts,
                    **scores,
                },
            )

            # --- report update goes HERE (still under the same lock) ---
            ex = final_result["example"]
            nq = final_result["num_qubits"]

            df = make_df_for_example_qubits(self.results, ex, nq)

            add_section(
                name=section_name(ex, nq),  # e.g. "adder_q4"
                title=section_title(ex, nq),  # e.g. "Adder - 4 qubits"
                df=df,
                numeric_cols={"Score", "Time Elapsed (min)"},
                root=self.report_root,
                level="section",
            )

            write_includes(root=self.report_root)

            if self.build_each_time:
                await asyncio.to_thread(build_report, self.report_root, True)
                print(
                    f"** Report updated: {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name}"
                )

            return final_result
