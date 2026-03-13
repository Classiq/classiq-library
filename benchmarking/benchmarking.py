from dataclasses import dataclass, field
import csv
import os
from pathlib import Path
import pandas as pd
import datetime
import asyncio
import abc
import traceback

from classiq import (
    create_model,
    synthesize_async,
    Preferences,
    set_quantum_program_execution_preferences,
    ExecutionPreferences,
    Constraints,
    QuantumProgram,
    ExecutionJob,
)
from hardwares_preferences import execution_preferences_wrapper
from reporting import *


RESULT_TIMEOUT = {"score": float("nan")}

#
# Locks
#
EXECUTION_SEMAPHORE = asyncio.Semaphore(3)
FILE_LOCK = asyncio.Lock()
REPORT_LOCK = asyncio.Lock()


class StageError(Exception):
    def __init__(self, stage: str, original: Exception):
        super().__init__(f"{stage} failed: {original}")
        self.stage = stage
        self.original = original


@dataclass
class BenchmarkExample(abc.ABC):
    name: str
    num_qubits: int
    constraints: Constraints = field(default_factory=Constraints)

    def __post_init__(self):
        self.main = self.create_main()

    @abc.abstractmethod
    def create_main(self) -> callable:
        pass

    @abc.abstractmethod
    async def submit(self, qprog: QuantumProgram) -> str:
        """
        Submit the execution and return a job_id.
        """
        pass

    async def get_job_result(self, job_id: str):
        """
        Helper for concrete benchmarks.
        Use this inside score() so retrieve-job failures are tagged correctly.
        """
        try:
            job = ExecutionJob.from_id(job_id)
            result = await job.result_async()
            return job, result
        except Exception as exc:
            raise StageError("retrieve_job", exc) from exc

    @abc.abstractmethod
    async def score(self, job_id: str) -> dict:
        """
        Return a dict like {"score": float}.
        This method is responsible for reading the job result
        and computing the benchmark score.
        """
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
        try:
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
        except Exception as exc:
            raise StageError("synthesis", exc) from exc

    async def submit_execution(self, example: BenchmarkExample) -> str:
        try:
            qprog = await self._synthesize(example)
            job_id = await example.submit(qprog)
            return job_id
        except StageError:
            raise
        except Exception as exc:
            raise StageError("submit_job", exc) from exc

    async def score(self, example: BenchmarkExample, job_id: str) -> dict:
        try:
            return await example.score(job_id)
        except StageError:
            raise
        except Exception as exc:
            raise StageError("score", exc) from exc

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
    if not os.path.exists(filename) or os.stat(filename).st_size == 0:
        return []

    results = []
    with open(filename, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            for k in ["num_qubits", "num_shots"]:
                if row.get(k):
                    row[k] = int(float(row[k]))

            for k in ["score", "execution_time"]:
                if row.get(k):
                    row[k] = float(row[k])

            for k in ["submitted_timestamp", "timestamp"]:
                if row.get(k):
                    row[k] = datetime.datetime.fromisoformat(row[k])

            results.append(row)
    return results


def dump_results(filename: str, results: list[dict]) -> None:
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    tmp_path = filename + ".tmp"

    if not results:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            pass
        os.replace(tmp_path, filename)
        return

    fieldnames = []
    for r in results:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
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
            rows.append(
                {
                    "Provider": r.get("backend_service_provider", ""),
                    "Backend Name": r.get("backend_name", ""),
                    "Score": r.get("score", float("nan")),
                    "Time Elapsed (min)": r.get("execution_time", float("nan")),
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
    log_filename: str | None = None

    def __post_init__(self):
        if self.log_filename is None:
            p = Path(self.filename)
            self.log_filename = str(p.with_suffix(p.suffix + ".errors.log"))

    async def reset_file(self) -> None:
        async with FILE_LOCK:
            dump_results(self.filename, [])

    def _append_error_log(
        self,
        stage: str,
        runner: HardwareRunner,
        example: BenchmarkExample,
        exc: Exception,
        job_id: str | None = None,
    ) -> None:
        Path(self.log_filename).parent.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now().isoformat(timespec="seconds")

        with open(self.log_filename, "a", encoding="utf-8") as f:
            f.write("=" * 100 + "\n")
            f.write(f"time: {now}\n")
            f.write(f"stage: {stage}\n")
            f.write(f"example: {example.name}\n")
            f.write(f"num_qubits: {example.num_qubits}\n")
            f.write(f"provider: {runner.backend_service_provider}\n")
            f.write(f"backend: {runner.backend_name}\n")
            f.write(f"num_shots: {runner.num_shots}\n")
            if job_id is not None:
                f.write(f"job_id: {job_id}\n")
            f.write(f"exception_type: {type(exc).__name__}\n")
            f.write(f"exception_message: {exc}\n")
            f.write("\nTRACEBACK\n")
            f.write(
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            )
            f.write("\n")

    async def _record_error(
        self,
        runner: HardwareRunner,
        example: BenchmarkExample,
        stage: str,
        exc: Exception,
        job_id: str | None = None,
        **extra_data,
    ) -> dict:
        self._append_error_log(stage, runner, example, exc, job_id=job_id)

        payload = {
            "status": "ERROR",
            "timestamp": datetime.datetime.now(),
            "job_id": job_id,
            "error_stage": stage,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            **extra_data,
        }

        try:
            return await self._upsert_and_write(runner, example, **payload)
        except Exception as write_exc:
            # If even the CSV write fails, at least log that too and return a best-effort dict.
            self._append_error_log(
                "write_error_record", runner, example, write_exc, job_id=job_id
            )
            return runner.to_dict(example, **payload)

    async def run(
        self, runner: HardwareRunner, example: BenchmarkExample
    ) -> dict | None:
        await EXECUTION_SEMAPHORE.acquire()
        try:
            #
            # Step 1 - load existing data, or submit if needed
            #
            try:
                existing_data = await self._load_existing_data(runner, example)
            except Exception as exc:
                return await self._record_error(runner, example, "load_results", exc)

            job_id = None

            if existing_data is None:
                try:
                    job_id = await self._submit_and_write(runner, example)
                except StageError as exc:
                    return await self._record_error(
                        runner, example, exc.stage, exc.original
                    )
                except Exception as exc:
                    return await self._record_error(runner, example, "submit_job", exc)
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
                elif existing_data["status"] == "ERROR":
                    print(
                        "Previous attempt ended with ERROR. We're NOT trying again automatically."
                    )
                    return existing_data
                else:
                    return await self._record_error(
                        runner,
                        example,
                        "load_results",
                        ValueError("Existing row has an unexpected status."),
                        job_id=existing_data.get("job_id"),
                    )

            #
            # Step 2 - Wait for execution and score
            #
            try:
                scores = await asyncio.wait_for(
                    runner.score(example, job_id),
                    timeout=runner.max_timeout,
                )
                status = "COMPLETED"
            except asyncio.TimeoutError:
                scores = RESULT_TIMEOUT
                status = "TIMEOUT"
            except StageError as exc:
                return await self._record_error(
                    runner, example, exc.stage, exc.original, job_id=job_id
                )
            except Exception as exc:
                return await self._record_error(
                    runner, example, "score", exc, job_id=job_id
                )

            completed_ts = datetime.datetime.now()
            print(
                f"{completed_ts}: Completed {example.name}-{example.num_qubits} "
                f"for {runner.backend_service_provider} - {runner.backend_name} "
                f"--> Score {scores}"
            )

            #
            # Step 3 - Write result
            #
            try:
                final_result = await self._upsert_and_write(
                    runner,
                    example,
                    status=status,
                    timestamp=completed_ts,
                    **scores,
                )
            except Exception as exc:
                return await self._record_error(
                    runner,
                    example,
                    "write_results",
                    exc,
                    job_id=job_id,
                    **scores,
                )

            #
            # Step 4 - Update report / build PDF (serialized)
            #
            try:
                async with REPORT_LOCK:
                    async with FILE_LOCK:
                        all_results = load_results(self.filename)

                    df = make_df_for_example_qubits(
                        all_results, example.name, example.num_qubits
                    )

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
                            f"** Report updated: {example.name}-{example.num_qubits} "
                            f"for {runner.backend_service_provider} - {runner.backend_name}"
                        )
            except Exception as exc:
                return await self._record_error(
                    runner,
                    example,
                    "report",
                    exc,
                    job_id=job_id,
                    **scores,
                )

            return final_result

        finally:
            EXECUTION_SEMAPHORE.release()

    async def _upsert_and_write(
        self, runner: HardwareRunner, example: BenchmarkExample, **extra_data
    ) -> dict:
        new_entry = runner.to_dict(example, **extra_data)
        base_dict = runner.to_dict(example)

        async with FILE_LOCK:
            results = load_results(self.filename)

            updated = False
            for i, res in enumerate(results):
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
            f"{submitted_ts}: Submit {example.name}-{example.num_qubits} "
            f"for {runner.backend_service_provider} - {runner.backend_name}"
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
