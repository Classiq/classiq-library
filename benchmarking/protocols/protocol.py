"""Quantum Volume benchmarking protocol.

Implements the QV protocol described in:
  Cross et al., "Validating quantum computers using randomized model circuits",
  Phys. Rev. A 100, 032328 (2019).  arXiv:1811.12926

Design notes
------------
1. **Non-consecutive passing widths.**  The standard QV definition (Eq. 7 of the
   paper) requires all widths up to n to pass for QV = 2^n.  This implementation
   intentionally relaxes that requirement: it reports QV = 2^(largest passing
   width) even if some intermediate widths failed.  The rationale is that a
   transient failure at an intermediate width (e.g. due to a temporary
   calibration drift) should not mask a device's demonstrated capability at
   higher widths.  Users who need the strict definition can inspect the
   per-width pass/fail table returned by `all_width_summaries()`.

2. **Shot-count sensitivity.**  The confidence bound follows Algorithm 1 of the
   paper (pooled binomial one-sided interval).  With low shot counts the
   statistical error grows quickly.  For n_s = 10 shots per circuit, assuming
   ideal heavy-output fraction h_d ~ 0.85 and sigma = 2:

       n_c (circuits) | error term  | lower bound | passes?
       ------------------------------------------------
            10        |   ~0.23     |   ~0.62     |  NO  (even ideal device fails)
            30        |   ~0.13     |   ~0.72     |  yes
           100        |   ~0.07     |   ~0.78     |  yes
           200        |   ~0.05     |   ~0.80     |  yes

   Therefore n_s >= 100 is recommended for reliable results; with n_s = 10 at
   least ~30 circuits are needed to pass the threshold even in the noiseless
   case.
"""

import sys

sys.path.insert(0, "..")
from collector import ResultCollector
from hardware import HardwareRunner
from storage import load_results
from reporting import write_includes, add_section, build_report, add_text_block
from qv_example import QVExample
import asyncio
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Maximum fraction of trials that may error out while still allowing a width
# to pass. For example, 0.15 means up to 15% of trials can fail.
MAX_TRIAL_ERROR_RATE = 0.15


@dataclass
class QuantumVolumeProtocol:
    """Orchestrates the Quantum Volume (QV) benchmarking protocol.

    The protocol sweeps over a range of circuit widths (number of qubits),
    runs multiple random QV trials per width on each backend, scores them
    using the heavy-output probability, and determines the largest width
    that passes the statistical threshold — the quantum volume is 2^(that width).
    """

    # --- Required parameters ---
    min_num_qubits: int  # Smallest circuit width to test
    max_num_qubits: int  # Largest circuit width to test
    num_trials: int  # Number of random QV circuits per width
    runners: list[HardwareRunner]  # Backend runners to benchmark

    # --- File and directory paths ---
    results_dir: str = "protocols/data"  # Where per-width CSV results are stored
    report_root: str = "../report"  # Root directory for LaTeX report output

    # --- Reproducibility ---
    base_seed: int = 1234  # Base seed; each trial derives a unique seed from this

    # --- Statistical thresholds ---
    # A width passes if the lower confidence bound of the mean heavy-output
    # probability exceeds success_threshold (default 2/3 per the QV definition).
    success_threshold: float = 2 / 3
    # Number of standard errors subtracted from the mean to form the lower bound.
    sigma_factor: float = 2.0
    # Maximum concurrent submitted jobs per results directory
    max_submitted_jobs_in_dir: int = 3

    # --- Report metadata ---
    report_family_title: str = "Quantum Volume"
    report_family_description: str = ""

    def widths(self) -> list[int]:
        """Return the list of circuit widths to sweep over."""
        return list(range(self.min_num_qubits, self.max_num_qubits + 1))

    def shots_label(self) -> str:
        """Human-readable label summarizing the shot counts across runners."""
        shots_values = sorted({runner.num_shots for runner in self.runners})
        if len(shots_values) == 1:
            return f"{shots_values[0]} shots"
        return "multiple shot counts"

    def filename_for_width(self, num_qubits: int) -> str:
        """CSV file path for storing results of a given width."""
        return str(Path(self.results_dir) / f"qv_{num_qubits}.csv")

    def collector_for_width(self, num_qubits: int) -> ResultCollector:
        """Create a ResultCollector that saves trial results for a given width."""
        return ResultCollector(
            filename=self.filename_for_width(num_qubits),
            skip_report=True,
            max_submitted_jobs_in_dir=self.max_submitted_jobs_in_dir,
        )

    def seed_for_trial(self, num_qubits: int, trial_id: int) -> int:
        """Deterministic seed for a specific (width, trial) pair."""
        return self.base_seed + 100_000 * num_qubits + trial_id

    def make_example(self, num_qubits: int, trial_id: int) -> QVExample:
        """Instantiate a QV circuit example for a given width and trial."""
        return QVExample(
            num_qubits=num_qubits,
            trial_id=trial_id,
            seed=self.seed_for_trial(num_qubits, trial_id),
        )

    async def reset_files(self) -> None:
        """Clear all per-width result files to start fresh."""
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        for num_qubits in self.widths():
            collector = self.collector_for_width(num_qubits)
            await collector.reset_file()

    async def run_width(self, num_qubits: int) -> list[dict | None]:
        """Submit and collect all trials for a single width across all runners."""
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        collector = self.collector_for_width(num_qubits)

        tasks = []
        for runner in self.runners:
            for trial_id in range(self.num_trials):
                example = self.make_example(num_qubits, trial_id)
                tasks.append(collector.run(runner, example))

        return await asyncio.gather(*tasks)

    async def run(self) -> dict[int, pd.DataFrame]:
        """Run the full protocol: sweep all widths sequentially, summarize each."""
        summaries: dict[int, pd.DataFrame] = {}

        for num_qubits in self.widths():
            await self.run_width(num_qubits)
            summaries[num_qubits] = self.summarize_width(num_qubits)

        return summaries

    def _load_width_df(self, num_qubits: int) -> pd.DataFrame:
        """Load raw trial results from the CSV file for a given width."""
        filename = Path(self.filename_for_width(num_qubits))
        if not filename.exists():
            return pd.DataFrame()

        results = load_results(str(filename))
        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    def summarize_width(self, num_qubits: int) -> pd.DataFrame:
        """Aggregate trial results for a single width into a per-backend summary.

        For each backend, computes:
          - mean, std, and stderr of the heavy-output probability
          - a lower confidence bound (mean - sigma_factor * stderr)
          - whether the width passes: enough trials completed (within
            MAX_TRIAL_ERROR_RATE tolerance) AND the lower bound exceeds 2/3
          - counts of trials by status (SUBMITTED, COMPLETED, TIMEOUT, ERROR)
        """
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

        # Count how many trials ended in each status per backend
        status_counts = (
            df.groupby(group_cols + ["status"], dropna=False)
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        completed = df[df["status"] == "COMPLETED"].copy()

        if completed.empty:
            # No trials completed — fill in zeros/NaNs and mark as not passed
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
            # Ensure num_shots is numeric for the pooled confidence bound
            if "num_shots" in completed.columns:
                completed["num_shots"] = pd.to_numeric(
                    completed["num_shots"], errors="coerce"
                )

            # Compute statistics of the heavy-output probability per backend
            score_summary = (
                completed.groupby(group_cols, dropna=False)[metric_col]
                .agg(num_completed="count", mean_score="mean", std_score="std")
                .reset_index()
            )

            score_summary["std_score"] = score_summary["std_score"].fillna(0.0)
            score_summary["stderr_score"] = score_summary["std_score"] / np.sqrt(
                score_summary["num_completed"]
            )

            # Lower confidence bound using the pooled binomial formula from
            # Algorithm 1 in Cross et al. (arXiv:1811.12926):
            #   (n_h - sigma * sqrt(n_h * (n_s - n_h / n_c))) / (n_c * n_s) > 2/3
            # where n_h = total heavy output counts across all circuits,
            #       n_c = number of circuits (trials),
            #       n_s = number of shots per circuit.
            def _pooled_lower_bound(group: pd.DataFrame) -> float:
                n_c = len(group)
                n_s_values = group["num_shots"].values
                # All trials for a given backend should have the same num_shots,
                # but handle the general case by summing per-trial heavy counts.
                h_per_trial = group[metric_col].values * n_s_values
                n_h = h_per_trial.sum()
                total_shots = n_s_values.sum()  # n_c * n_s when uniform
                if total_shots == 0:
                    return 0.0
                variance_term = n_h * (total_shots - n_h / n_c)
                if variance_term < 0:
                    variance_term = 0.0
                return (n_h - self.sigma_factor * np.sqrt(variance_term)) / total_shots

            if "num_shots" in completed.columns:
                lcb = (
                    completed.groupby(group_cols, dropna=False)
                    .apply(_pooled_lower_bound)
                    .reset_index(name="lower_confidence_bound")
                )
                score_summary = score_summary.merge(lcb, on=group_cols, how="left")
            else:
                # Fallback to normal approximation if num_shots is unavailable
                score_summary["lower_confidence_bound"] = (
                    score_summary["mean_score"]
                    - self.sigma_factor * score_summary["stderr_score"]
                )
            score_summary["num_qubits"] = num_qubits
            score_summary["num_trials_requested"] = self.num_trials

            # A width passes if:
            #   1. Enough trials completed (within MAX_TRIAL_ERROR_RATE tolerance)
            #   2. The lower confidence bound exceeds the success threshold (2/3)
            min_completed = int(np.ceil(self.num_trials * (1 - MAX_TRIAL_ERROR_RATE)))
            score_summary["passed"] = (
                score_summary["num_completed"] >= min_completed
            ) & (score_summary["lower_confidence_bound"] > self.success_threshold)

            # Merge status counts with score statistics
            summary = status_counts.merge(
                score_summary,
                on=group_cols,
                how="outer",
            )

            # Fill NaNs for backends that appear in one table but not the other
            summary["num_qubits"] = summary["num_qubits"].fillna(num_qubits)
            summary["num_trials_requested"] = summary["num_trials_requested"].fillna(
                self.num_trials
            )
            summary["num_completed"] = summary["num_completed"].fillna(0).astype(int)
            summary["passed"] = summary["passed"].fillna(False)

        # Ensure all expected status columns exist and rename to count_<STATUS>.
        # Drop any unexpected status columns that leaked in from unstack.
        expected_statuses = ["SUBMITTED", "COMPLETED", "TIMEOUT", "ERROR"]
        for status in expected_statuses:
            if status not in summary.columns:
                summary[status] = 0
            summary[f"count_{status}"] = summary[status].astype(int)
        unexpected_status_cols = [
            col
            for col in summary.columns
            if col not in expected_statuses
            and col not in [f"count_{s}" for s in expected_statuses]
            and col in status_counts.columns
            and col not in ["backend_service_provider", "backend_name"]
        ]
        summary = summary.drop(columns=unexpected_status_cols + expected_statuses)

        # Select and order the final output columns
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
        """Concatenate per-width summaries for all widths into a single DataFrame."""
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
        """Determine the quantum volume for each backend.

        For each backend, finds the largest width that passed and computes
        QV = 2^(largest_passing_width). Note: this currently takes the max
        of all passing widths without requiring consecutive passes from
        min_num_qubits upward.
        """
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
        """Compute total execution time per (backend, width) for completed trials."""
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
        """Sum execution times across all widths for each backend."""
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
        """Combine quantum volume and total runtime into a single summary."""
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
        """Build a human-readable summary table for the LaTeX report.

        Joins quantum volume, trial completion counts, and average execution
        times into a single DataFrame with presentation-friendly column names.
        """
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

        # Aggregate trial counts across all widths per backend (e.g. "87/90")
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

        # Compute average execution time per trial across all widths
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
        """Write the QV summary to CSV, update LaTeX report sections, and
        optionally compile the PDF."""
        df = self.report_summary()

        root = Path(self.report_root)
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        csv_path = data_dir / "quantum_volume.csv"
        df.to_csv(csv_path, index=False)

        add_text_block(
            name="20_quantum_volume",
            title=self.report_family_title,
            text=self.report_family_description,
            root=str(root),
            level="section",
        )

        add_section(
            name="20_quantum_volume_summary",
            title=f"{self.min_num_qubits}--{self.max_num_qubits} qubits ({self.num_trials} trials, {self.shots_label()})",
            df=df,
            numeric_cols={"Quantum Volume", "Average Elapsed Time (min)"},
            root=str(root),
            level="subsection",
        )

        write_includes(root=str(root))

        if build:
            await asyncio.to_thread(build_report, str(root), True)

        return df
