from dataclasses import dataclass

import datetime
import asyncio
import traceback

from reporting import *
from pathlib import Path

from benchmark import BenchmarkExample
from hardware import HardwareRunner
from errors import StageError, RESULT_TIMEOUT
from storage import (
    load_results,
    make_df_for_example_qubits,
    section_name,
    dump_results,
    section_title,
    count_submitted_jobs_in_dir,
)

#
# Locks
#
EXECUTION_SEMAPHORE = asyncio.Semaphore(8)
FILE_LOCK = asyncio.Lock()
REPORT_LOCK = asyncio.Lock()

SUBMISSION_LOCK = asyncio.Lock()


@dataclass
class ResultCollector:
    filename: str
    report_root: str = "../report"
    build_each_time: bool = False
    log_filename: str | None = None
    skip_report: bool = False

    # New
    max_submitted_jobs_in_dir: int | None = 3
    data_dir: str | None = None

    def __post_init__(self):
        p = Path(self.filename)

        if self.log_filename is None:
            self.log_filename = str(p.with_suffix(p.suffix + ".errors.log"))

        if self.data_dir is None:
            self.data_dir = str(p.parent)

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
            "timestamp": datetime.datetime.now(),  # note this is the time in which the result was received. The job time is returned with the score.
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

    async def _submit_if_capacity_available(
        self,
        runner: HardwareRunner,
        example: BenchmarkExample,
    ) -> str | None:
        # No directory-level limit configured
        if self.max_submitted_jobs_in_dir is None:
            return await self._submit_and_write(runner, example)

        async with SUBMISSION_LOCK:
            async with FILE_LOCK:
                num_submitted = count_submitted_jobs_in_dir(self.data_dir)

            if num_submitted >= self.max_submitted_jobs_in_dir:
                print(
                    f"Submission budget full in {self.data_dir}: "
                    f"{num_submitted}/{self.max_submitted_jobs_in_dir} jobs are already SUBMITTED. "
                    f"Skipping new submission for now."
                )
                return None

            return await self._submit_and_write(runner, example)

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
                    job_id = await self._submit_if_capacity_available(runner, example)
                    if job_id is None:
                        return None
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
            if not self.skip_report:
                try:
                    async with REPORT_LOCK:
                        async with FILE_LOCK:
                            all_results = load_results(self.filename)

                        df = make_df_for_example_qubits(
                            all_results, example.name, example.num_qubits
                        )

                        # set num_shots for subtitle
                        matching_results = [
                            r
                            for r in all_results
                            if r.get("example") == example.name
                            and r.get("num_qubits") == example.num_qubits
                        ]

                        shots_values = sorted(
                            {
                                r.get("num_shots")
                                for r in matching_results
                                if r.get("num_shots") is not None
                            }
                        )

                        title = example.report_instance_title
                        if len(shots_values) == 1:
                            title += f" ({shots_values[0]} shots)"

                        add_text_block(
                            name=f"10_{example.name}",
                            title=example.report_family_title,
                            text=example.report_family_description,
                            root=self.report_root,
                            level="section",
                        )

                        add_section(
                            name=f"10_{example.name}_{example.num_qubits:03d}",
                            title=title,
                            df=df,
                            numeric_cols={
                                "Score",
                                "Time Elapsed (min)",
                                "Depth",
                                "2Q Gate Count",
                            },
                            root=self.report_root,
                            level="subsection",
                        )

                        write_includes(root=self.report_root)

                        if self.build_each_time:
                            await asyncio.to_thread(
                                build_report, self.report_root, True
                            )
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
        job_id, metrics = await runner.submit_execution(example)

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
            **metrics,
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

    async def print_status(self) -> None:
        async with FILE_LOCK:
            results = load_results(self.filename)

        print("=" * 10 + f" ({datetime.datetime.now()})   " + "=" * 10)
        if not results:
            print("No jobs recorded.")
            return

        for res in results:
            status = res.get("status", "")
            prefix = (
                f"{res.get('example')}-{res.get('num_qubits')} | "
                f"{res.get('backend_service_provider')} - {res.get('backend_name')}"
            )

            if status == "COMPLETED":
                score = res.get("score")
                exe_time_min = res.get("execution_time")
                print(
                    f"{prefix} | COMPLETED | score={score:.4f} | time={exe_time_min:.2f} min"
                )
            elif status == "SUBMITTED":
                print(f"{prefix} | {status} | at={res.get('submitted_timestamp')}")
            elif status == "ERROR" or status == "TIMEOUT":
                print(f"{prefix} | {status} ")
            else:
                print(f"{prefix} | {status} | Not submitted yet")
