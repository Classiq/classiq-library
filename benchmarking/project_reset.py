from pathlib import Path
import shutil

from reporting import reset_report

PROJECT_ROOT = Path(__file__).resolve().parent


def clear_directory_files(path: str | Path) -> None:
    path = Path(path)
    if not path.exists():
        return

    for child in path.iterdir():
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def reset_benchmark_project(
    report_root: str | Path = PROJECT_ROOT / "report",
    benchmarks_data_dir: str | Path = PROJECT_ROOT / "benchmarks" / "data",
    protocols_data_dir: str | Path = PROJECT_ROOT / "protocols" / "results",
) -> None:
    reset_report(report_root)
    clear_directory_files(benchmarks_data_dir)
    clear_directory_files(protocols_data_dir)
