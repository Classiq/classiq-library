import sys

sys.path.insert(0, "..")
from collector import ResultCollector
from hardware import HardwareRunner
from storage import load_results
from reporting import write_includes, add_section, build_report
from qv_example import QVExample
import asyncio
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class QuantumVolumeProtocol:
    min_num_qubits: int
    max_num_qubits: int
    num_trials: int
    runners: list[HardwareRunner]

    results_dir: str = "protocols/data"
    report_root: str = "../report"
    base_seed: int = 1234

    success_threshold: float = 2 / 3
    sigma_factor: float = 2.0
    max_submitted_jobs_in_dir: int = 3

    def widths(self) -> list[int]:
        return list(range(self.min_num_qubits, self.max_num_qubits + 1))

    def filename_for_width(self, num_qubits: int) -> str:
        return str(Path(self.results_dir) / f"qv_{num_qubits}.csv")

    def collector_for_width(self, num_qubits: int) -> ResultCollector:
        return ResultCollector(
            filename=self.filename_for_width(num_qubits),
            skip_report=True,
            max_submitted_jobs_in_dir=self.max_submitted_jobs_in_dir,
        )

    def seed_for_trial(self, num_qubits: int, trial_id: int) -> int:
        return self.base_seed + 100_000 * num_qubits + trial_id

    def make_example(self, num_qubits: int, trial_id: int) -> QVExample:
        return QVExample(
            num_qubits=num_qubits,
            trial_id=trial_id,
            seed=self.seed_for_trial(num_qubits, trial_id),
        )

    async def reset_files(self) -> None:
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        for num_qubits in self.widths():
            collector = self.collector_for_width(num_qubits)
            await collector.reset_file()

    async def run_width(self, num_qubits: int) -> list[dict | None]:
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        collector = self.collector_for_width(num_qubits)

        tasks = []
        for runner in self.runners:
            for trial_id in range(self.num_trials):
                example = self.make_example(num_qubits, trial_id)
                tasks.append(collector.run(runner, example))

        return await asyncio.gather(*tasks)

    async def run(self) -> dict[int, pd.DataFrame]:
        summaries: dict[int, pd.DataFrame] = {}

        for num_qubits in self.widths():
            await self.run_width(num_qubits)
            summaries[num_qubits] = self.summarize_width(num_qubits)

        return summaries

    def _load_width_df(self, num_qubits: int) -> pd.DataFrame:
        filename = Path(self.filename_for_width(num_qubits))
        if not filename.exists():
            return pd.DataFrame()

        results = load_results(str(filename))
        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    def summarize_width(self, num_qubits: int) -> pd.DataFrame:
        df = self._load_width_df(num_qubits)

        out_cols = [
            "num_qubits",
            "backend_service_provider",
            "backend_name",
            "num_trials_requested",
            "num_completed",
            "mean_score",
            "std_score",
            "stderr_score",
            "lower_confidence_bound",
            "passed",
            "count_SUBMITTED",
            "count_COMPLETED",
            "count_TIMEOUT",
            "count_ERROR",
        ]

        if df.empty:
            return pd.DataFrame(columns=out_cols)

        group_cols = ["backend_service_provider", "backend_name"]

        metric_col = "heavy_output_probability"

        if metric_col in df.columns:
            df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")

        status_counts = (
            df.groupby(group_cols + ["status"], dropna=False)
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        completed = df[df["status"] == "COMPLETED"].copy()

        if completed.empty:
            summary = status_counts.copy()
            summary["num_qubits"] = num_qubits
            summary["num_trials_requested"] = self.num_trials
            summary["num_completed"] = 0
            summary["mean_score"] = np.nan
            summary["std_score"] = np.nan
            summary["stderr_score"] = np.nan
            summary["lower_confidence_bound"] = np.nan
            summary["passed"] = False
        else:
            score_summary = (
                completed.groupby(group_cols, dropna=False)[metric_col]
                .agg(num_completed="count", mean_score="mean", std_score="std")
                .reset_index()
            )

            score_summary["std_score"] = score_summary["std_score"].fillna(0.0)
            score_summary["stderr_score"] = score_summary["std_score"] / np.sqrt(
                score_summary["num_completed"]
            )
            score_summary["lower_confidence_bound"] = (
                score_summary["mean_score"]
                - self.sigma_factor * score_summary["stderr_score"]
            )
            score_summary["num_qubits"] = num_qubits
            score_summary["num_trials_requested"] = self.num_trials
            score_summary["passed"] = (
                score_summary["num_completed"] == self.num_trials
            ) & (score_summary["lower_confidence_bound"] > self.success_threshold)

            summary = status_counts.merge(
                score_summary,
                on=group_cols,
                how="outer",
            )

            summary["num_qubits"] = summary["num_qubits"].fillna(num_qubits)
            summary["num_trials_requested"] = summary["num_trials_requested"].fillna(
                self.num_trials
            )
            summary["num_completed"] = summary["num_completed"].fillna(0).astype(int)
            summary["passed"] = summary["passed"].fillna(False)

        for status in ["SUBMITTED", "COMPLETED", "TIMEOUT", "ERROR"]:
            if status not in summary.columns:
                summary[status] = 0
            summary[f"count_{status}"] = summary[status].astype(int)

        summary = summary[
            [
                "num_qubits",
                "backend_service_provider",
                "backend_name",
                "num_trials_requested",
                "num_completed",
                "mean_score",
                "std_score",
                "stderr_score",
                "lower_confidence_bound",
                "passed",
                "count_SUBMITTED",
                "count_COMPLETED",
                "count_TIMEOUT",
                "count_ERROR",
            ]
        ].sort_values(
            by=["backend_service_provider", "backend_name"],
            kind="stable",
        )

        return summary.reset_index(drop=True)

    def all_width_summaries(self) -> pd.DataFrame:
        dfs = []
        for num_qubits in self.widths():
            s = self.summarize_width(num_qubits)
            if not s.empty:
                dfs.append(s)

        if not dfs:
            return pd.DataFrame(
                columns=[
                    "num_qubits",
                    "backend_service_provider",
                    "backend_name",
                    "num_trials_requested",
                    "num_completed",
                    "mean_score",
                    "std_score",
                    "stderr_score",
                    "lower_confidence_bound",
                    "passed",
                    "count_SUBMITTED",
                    "count_COMPLETED",
                    "count_TIMEOUT",
                    "count_ERROR",
                ]
            )

        return pd.concat(dfs, ignore_index=True)

    def quantum_volume_summary(self) -> pd.DataFrame:
        df = self.all_width_summaries()

        out_cols = [
            "backend_service_provider",
            "backend_name",
            "largest_passing_width",
            "quantum_volume",
        ]

        if df.empty:
            return pd.DataFrame(columns=out_cols)

        rows = []
        for (provider, backend), g in df.groupby(
            ["backend_service_provider", "backend_name"],
            dropna=False,
        ):
            passed_widths = g.loc[g["passed"], "num_qubits"].tolist()
            largest_passing_width = max(passed_widths) if passed_widths else 0

            rows.append(
                {
                    "backend_service_provider": provider,
                    "backend_name": backend,
                    "largest_passing_width": largest_passing_width,
                    "quantum_volume": (
                        2**largest_passing_width if largest_passing_width > 0 else 1
                    ),
                }
            )

        return (
            pd.DataFrame(rows)
            .sort_values(
                by=["backend_service_provider", "backend_name"],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    def runtime_summary(self) -> pd.DataFrame:
        dfs = []

        for num_qubits in self.widths():
            df = self._load_width_df(num_qubits)
            if df.empty or "execution_time" not in df.columns:
                continue

            completed = df[df["status"] == "COMPLETED"].copy()
            if completed.empty:
                continue

            completed["execution_time"] = pd.to_numeric(
                completed["execution_time"],
                errors="coerce",
            )

            summary = (
                completed.groupby(
                    ["backend_service_provider", "backend_name"],
                    dropna=False,
                )["execution_time"]
                .sum()
                .reset_index()
            )
            summary["num_qubits"] = num_qubits
            dfs.append(summary)

        if not dfs:
            return pd.DataFrame(
                columns=[
                    "backend_service_provider",
                    "backend_name",
                    "num_qubits",
                    "execution_time",
                ]
            )

        return pd.concat(dfs, ignore_index=True)

    def total_runtime_summary(self) -> pd.DataFrame:
        df = self.runtime_summary()
        if df.empty:
            return pd.DataFrame(
                columns=[
                    "backend_service_provider",
                    "backend_name",
                    "total_execution_time",
                ]
            )

        return (
            df.groupby(
                ["backend_service_provider", "backend_name"],
                dropna=False,
            )["execution_time"]
            .sum()
            .reset_index()
            .rename(columns={"execution_time": "total_execution_time"})
            .sort_values(
                by=["backend_service_provider", "backend_name"],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    def final_summary(self) -> pd.DataFrame:
        qv = self.quantum_volume_summary()
        rt = self.total_runtime_summary()

        if qv.empty:
            return qv

        return (
            qv.merge(
                rt,
                on=["backend_service_provider", "backend_name"],
                how="left",
            )
            .sort_values(
                by=["backend_service_provider", "backend_name"],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    def report_summary(self) -> pd.DataFrame:
        width_df = self.all_width_summaries()
        qv_df = self.quantum_volume_summary()

        if width_df.empty or qv_df.empty:
            return pd.DataFrame(
                columns=[
                    "Provider",
                    "Backend",
                    "Quantum Volume",
                    "Trials",
                    "Average Elapsed Time (min)",
                ]
            )

        trials_df = (
            width_df.groupby(
                ["backend_service_provider", "backend_name"],
                dropna=False,
            )[["num_completed", "num_trials_requested"]]
            .sum()
            .reset_index()
        )
        trials_df["Trials"] = (
            trials_df["num_completed"].astype(int).astype(str)
            + "/"
            + trials_df["num_trials_requested"].astype(int).astype(str)
        )

        runtime_rows = []
        for num_qubits in self.widths():
            df = self._load_width_df(num_qubits)
            if df.empty or "execution_time" not in df.columns:
                continue

            completed = df[df["status"] == "COMPLETED"].copy()
            if completed.empty:
                continue

            completed["execution_time"] = pd.to_numeric(
                completed["execution_time"], errors="coerce"
            )

            runtime_rows.append(
                completed[
                    ["backend_service_provider", "backend_name", "execution_time"]
                ]
            )

        if runtime_rows:
            runtime_df = pd.concat(runtime_rows, ignore_index=True)
            runtime_df = (
                runtime_df.groupby(
                    ["backend_service_provider", "backend_name"],
                    dropna=False,
                )["execution_time"]
                .mean()
                .reset_index()
                .rename(columns={"execution_time": "Average Elapsed Time (min)"})
            )
            runtime_df["Average Elapsed Time (min)"] = runtime_df[
                "Average Elapsed Time (min)"
            ].round(2)
        else:
            runtime_df = pd.DataFrame(
                columns=[
                    "backend_service_provider",
                    "backend_name",
                    "Average Elapsed Time (min)",
                ]
            )

        out = (
            qv_df.merge(
                trials_df[
                    [
                        "backend_service_provider",
                        "backend_name",
                        "Trials",
                    ]
                ],
                on=["backend_service_provider", "backend_name"],
                how="left",
            )
            .merge(
                runtime_df,
                on=["backend_service_provider", "backend_name"],
                how="left",
            )
            .rename(
                columns={
                    "backend_service_provider": "Provider",
                    "backend_name": "Backend",
                    "quantum_volume": "Quantum Volume",
                }
            )
        )

        return (
            out[
                [
                    "Provider",
                    "Backend",
                    "Quantum Volume",
                    "Trials",
                    "Average Elapsed Time (min)",
                ]
            ]
            .sort_values(["Provider", "Backend"], kind="stable")
            .reset_index(drop=True)
        )

    async def update_report(self, build: bool = False) -> pd.DataFrame:
        df = self.report_summary()

        root = Path(self.report_root)
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        csv_path = data_dir / "quantum_volume.csv"
        df.to_csv(csv_path, index=False)

        add_section(
            name="quantum_volume",
            title=f"Quantum Volume {self.min_num_qubits}--{self.max_num_qubits} ({self.num_trials} trails)",
            df=df,
            numeric_cols={"Quantum Volume", "Average Elapsed Time (min)"},
            root=str(root),
            level="section",
        )

        write_includes(root=str(root))

        if build:
            await asyncio.to_thread(build_report, str(root), True)

        return df
