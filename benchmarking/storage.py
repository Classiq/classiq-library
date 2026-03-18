import csv
import os
import datetime

from reporting import *
from collections import Counter
from pathlib import Path


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


def status_counts_in_dir(data_dir: str | Path) -> dict[str, int]:
    counts = Counter()
    data_dir = Path(data_dir)

    if not data_dir.exists():
        return {}

    for path in data_dir.glob("*.csv"):
        try:
            results = load_results(str(path))
        except Exception:
            continue

        for res in results:
            status = res.get("status")
            if status is not None:
                counts[status] += 1

    return dict(counts)


def count_submitted_jobs_in_dir(data_dir: str | Path) -> int:
    return status_counts_in_dir(data_dir).get("SUBMITTED", 0)


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
