from dataclasses import dataclass, field
import csv
import os
from pathlib import Path
import pandas as pd
import datetime
import asyncio

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


#
# Utility functions & CSV I/O
#
def load_results(filename: str) -> list[dict]:
    """Reads the CSV and converts numerical/datetime strings back to objects."""
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        return []

    results = []
    with open(filename, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Restore types dynamically
            for k in ["num_qubits", "num_shots"]:
                if row.get(k):
                    row[k] = int(float(row[k]))
            if row.get("score"):
                row["score"] = float(row["score"])
            for k in ["submitted_timestamp", "timestamp"]:
                if row.get(k):
                    row[k] = datetime.datetime.fromisoformat(row[k])

            results.append(row)
    return results


def dump_results(filename: str, results: list[dict]) -> None:
    """Safely writes a list of dicts to CSV via an atomic replacement."""
    if not results:
        return

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    tmp_path = filename + ".tmp"

    # Extract keys from the first dictionary to use as CSV headers
    fieldnames = list(results[0].keys())

    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            # Convert datetimes to isoformat strings for clean saving
            row = {
                k: (v.isoformat() if isinstance(v, datetime.datetime) else v)
                for k, v in r.items()
            }
            writer.writerow(row)

    os.replace(tmp_path, filename)


def make_df_for_example_qubits(
    results: list[dict], example_name: str, num_qubits: int
) -> pd.DataFrame:
    rows = []
    for r in results:
        if (
            r.get("example") == example_name
            and r.get("num_qubits") == num_qubits
            and r.get("status") in {"COMPLETED", "TIMEOUT", "ERROR"}
        ):
            sub, comp = r.get("submitted_timestamp"), r.get("timestamp")
            elapsed_min = (
                (comp - sub).total_seconds() / 60.0 if (sub and comp) else None
            )

            rows.append(
                {
                    "Provider": r.get("backend_service_provider", ""),
                    "Backend Name": r.get("backend_name", ""),
                    "Score": r.get("score", float("nan")),
                    "Time Elapsed (min)": elapsed_min,
                }
            )

    df = pd.DataFrame(rows)
    if not df.empty:
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


#
# Collector
#
@dataclass
class ResultCollector:
    filename: str
    report_root: str = "../report"
    build_each_time: bool = False

    async def run(
        self, runner: HardwareRunner, example: BenchmarkExample
    ) -> dict | None:
        #
        # Step 1 - load existing data, or submit if needed
        #
        existing_data = await self._load_existing_data(runner, example)

        if existing_data is None:
            job_id = await self._submit_and_write(runner, example)
        else:
            if existing_data["status"] == "COMPLETED":
                return existing_data
            elif existing_data["status"] == "SUBMITTED":
                job_id = existing_data["job_id"]
            elif existing_data["status"] == "TIMEOUT":
                print(
                    "Previous attempt timed out. We're NOT trying again automatically."
                )
                return None
            else:
                raise ValueError(
                    "Weird case. There is already an entry, and it's not COMPLETED and not SUBMITTED."
                )

        #
        # Step 2 - Wait for execution and Score
        #
        try:
            score = await asyncio.wait_for(
                runner.score(example, job_id),
                timeout=runner.max_timeout,
            )
            status = "COMPLETED"
        except asyncio.TimeoutError:
            score = RESULT_TIMEOUT
            status = "TIMEOUT"

        completed_ts = datetime.datetime.now()
        print(
            f"{completed_ts}: Completed {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name} --> Score {score}"
        )

        #
        # Step 3 - Write result & Generate pdf
        #
        final_result = await self._upsert_and_write(
            runner,
            example,
            status=status,
            score=score,
            timestamp=completed_ts,
        )

        # --- Generate Report ---
        async with FILE_LOCK:
            all_results = load_results(self.filename)

        df = make_df_for_example_qubits(all_results, example.name, example.num_qubits)

        add_section(
            name=section_name(example.name, example.num_qubits),
            title=section_title(example.name, example.num_qubits),
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

    async def _upsert_and_write(
        self, runner: HardwareRunner, example: BenchmarkExample, **extra_data
    ) -> dict:
        """Updates an existing entry or appends a new one to prevent duplicate rows."""
        new_entry = runner.to_dict(example, **extra_data)
        base_dict = runner.to_dict(example)

        async with FILE_LOCK:
            results = load_results(self.filename)

            updated = False
            for i, res in enumerate(results):
                # If the base attributes match, this is our row to update
                if base_dict.items() <= res.items():
                    results[i].update(new_entry)
                    new_entry = results[i]
                    updated = True
                    break

            if not updated:
                results.append(new_entry)

            dump_results(self.filename, results)

        return new_entry

    async def _submit_and_write(
        self, runner: HardwareRunner, example: BenchmarkExample
    ) -> str:
        job_id = await runner.submit_execution(example)

        submitted_ts = datetime.datetime.now()
        print(
            f"{submitted_ts}: Submit {example.name}-{example.num_qubits} for {runner.backend_service_provider} - {runner.backend_name}"
        )

        await self._upsert_and_write(
            runner,
            example,
            status="SUBMITTED",
            job_id=job_id,
            submitted_timestamp=submitted_ts,
        )
        return job_id

    async def _load_existing_data(
        self, runner: HardwareRunner, example: BenchmarkExample
    ) -> dict | None:
        example_dict = runner.to_dict(example)

        async with FILE_LOCK:
            results = load_results(self.filename)

        for res in results:
            if example_dict.items() <= res.items():
                return res
        return None
