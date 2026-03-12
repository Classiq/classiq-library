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
import abc


RESULT_TIMEOUT = float("nan")

#
# Locks
#
EXECUTION_SEMAPHORE = asyncio.Semaphore(3)
FILE_LOCK = asyncio.Lock()


@dataclass
class BenchmarkExample(abc.ABC):
    name: str
    num_qubits: int
    constraints: Constraints = field(
        default_factory=Constraints
    )  # constraints for synthesis

    def __post_init__(self):
        self.main = self.create_main()

    @abc.abstractmethod
    def create_main(self) -> callable:  # () -> main
        pass

    @abc.abstractmethod
    async def execute(self, qprog: QuantumProgram) -> str:  # (qprog) -> job.id
        pass

    @abc.abstractmethod
    def score(self, df: pandas.DataFrame) -> float:  # (result_dataframe) -> float
        pass


@dataclass
class HardwareRunner:
    backend_service_provider: str
    backend_name: str
    max_timeout: int  # seconds
    num_shots: int
    backend_kwargs: dict = field(default_factory=dict)

    @property
    def _synthesis_preferences(self) -> Preferences:
        if self.backend_service_provider == "Classiq":
            return Preferences()
        else:
            return Preferences(
                backend_service_provider=self.backend_service_provider,
                backend_name=self.backend_name,
            )

    @property
    def _execution_preferences(self):
        return ExecutionPreferences(
            num_shots=self.num_shots,
            backend_preferences=execution_preferences_wrapper(
                self.backend_service_provider,
                self.backend_name,
                **self.backend_kwargs,
            ),
        )

    async def _synthesize(self, example: BenchmarkExample) -> QuantumProgram:
        qmod = create_model(
            example.main,
            preferences=self._synthesis_preferences,
            constraints=example.constraints,
        )
        qprog = await synthesize_async(qmod)
        qprog = set_quantum_program_execution_preferences(
            qprog, self._execution_preferences
        )
        return qprog

    async def submit_execution(self, example: BenchmarkExample) -> str:
        qprog = await self._synthesize(example)

        await EXECUTION_SEMAPHORE.acquire()
        try:
            job_id = await example.execute(qprog)
        finally:
            EXECUTION_SEMAPHORE.release()

        return job_id

    async def score(self, example: BenchmarkExample, job_id: str) -> float:
        job = ExecutionJob.from_id(job_id)
        result = await job.result_async()

        df = result[0].value.dataframe
        return await example.score(df)

    def to_dict(self, example: BenchmarkExample, **kwargs):
        return {
            "example": example.name,
            "num_qubits": example.num_qubits,
            "backend_service_provider": self.backend_service_provider,
            "backend_name": self.backend_name,
            "num_shots": self.num_shots,
            **kwargs,
        }


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
        FILE_LOCK = asyncio.Lock()
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
        async with FILE_LOCK:
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
            job_id = await runner.submit_execution(example)
            submitted_ts = datetime.datetime.now()
            print(
                f"{submitted_ts}: Submit {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name}"
            )

            async with FILE_LOCK:
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
            score = await asyncio.wait_for(
                runner.score(example, job_id),
                timeout=runner.max_timeout,
            )
            status = "COMPLETED"
        except asyncio.TimeoutError:
            score = RESULT_TIMEOUT
            status = "TIMEOUT"

        scores = {"score": score}

        completed_ts = datetime.datetime.now()
        print(
            f"{completed_ts}: Completed {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name} --> Score {scores}"
        )

        # 4) Finalize + write (quick, under lock)
        async with FILE_LOCK:
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
