"""
Generate native .qmod files from Classiq Jupyter notebooks.

For every call to classiq.synthesize() encountered while running a notebook,
a native .qmod file is written to disk.  The backend is never contacted —
synthesize() and execute() are replaced with mocks so notebooks run quickly
and cell errors from mocked results do not block later synthesis calls.

WHAT GETS COLLECTED
  Every .ipynb notebook found under the given paths (recursive directory scan),
  provided a <notebook-stem>.metadata.json file exists in the same directory.
  The metadata file is the marker that a notebook is a canonical, library-managed
  notebook intended for qmod generation; notebooks without one are skipped.
  Individual .py scripts may also be passed explicitly on the command line, but
  .py files are never collected automatically from a directory — a directory may
  contain library code, utilities, and test files that are not Classiq scripts.
  Each notebook/script produces at most one .qmod file; if synthesize() is called
  more than once, only the last call's model is kept.

OUTPUT
  Models are written next to each source notebook/script as
      <notebook-stem>.qmod
  A <notebook-stem>.synthesis_options.json sidecar is always written alongside
  the .qmod file, containing only the synthesis constraints and preferences
  that the notebook explicitly overrides.  Fields left at their classiq SDK
  default are omitted to keep the sidecar minimal.

HAND-WRITTEN .qmod FILES
  If a <notebook-stem>.qmod already exists in the source directory and contains
  an inline comment (// …), it is treated as hand-written and left untouched.
  Inline comments are never produced by write_qmod(), so their presence is a
  reliable signal that the file was crafted by hand.
  Pass --force to override this protection and regenerate the file anyway.

USAGE EXAMPLES
  # Run with defaults: scan algorithms/ and applications/ in the current directory
  python scripts/generate_qmod_from_notebooks.py

  # Explicit top-level directories
  python scripts/generate_qmod_from_notebooks.py algorithms/ applications/

  # Any sub-directory (partial path is fine)
  python scripts/generate_qmod_from_notebooks.py applications/chemistry applications/cfd/qlbm

  # Individual files (.ipynb or .py)
  python scripts/generate_qmod_from_notebooks.py algorithms/foundational/grover/grover.ipynb

  # A text file listing what to run  (one entry per line, same rules as above)
  python scripts/generate_qmod_from_notebooks.py --from-file my_list.txt

  # Change parallelism
  python scripts/generate_qmod_from_notebooks.py --workers 4 algorithms/

  # Regenerate even hand-written .qmod files
  python scripts/generate_qmod_from_notebooks.py --force functions/
"""

import argparse
import glob
import os
import resource
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Each parallel Jupyter kernel opens ~5 ZMQ sockets; macOS defaults to 256
# open files per process, which is easily exhausted when running many kernels.
# Raise the soft limit to 4096 (capped at the hard limit) before starting.
try:
    _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(4096, _hard), _hard))
except (ValueError, OSError):
    pass

# ---------------------------------------------------------------------------
# Patch injected as the first cell / prepended to every script
# ---------------------------------------------------------------------------
PATCH = """\
# ============================================================
# classiq model-saver patch  (injected by generate_qmod_from_notebooks.py)
# ============================================================
import json as _json
import os
from pathlib import Path
from unittest.mock import MagicMock

import classiq as _cq
import classiq.synthesis as _cq_syn
from classiq import Constraints as _Constraints, Preferences as _Preferences
from classiq.qmod.write_qmod import write_qmod

_DEFAULT_CONSTRAINTS = _Constraints().model_dump(exclude_none=True)
_DEFAULT_PREFERENCES = _Preferences().model_dump(exclude_none=True)
_DEFAULT_PREFERENCES.pop("random_seed", None)  # generated fresh each run; not a user-chosen value


def _strip_defaults(value, default):
    \"\"\"Recursively drop dict entries equal to default; treat string lists as sets.\"\"\"
    if isinstance(value, dict) and isinstance(default, dict):
        out = {}
        for k, v in value.items():
            s = _strip_defaults(v, default.get(k))
            if s is not None:
                out[k] = s
        return out or None
    if isinstance(value, list) and isinstance(default, list):
        all_str = all(isinstance(x, str) for x in value) and all(isinstance(x, str) for x in default)
        if all_str:
            if sorted(value) == sorted(default):
                return None
            return sorted(value)
        return None if value == default else value
    return None if value == default else value


def _patched_synthesize(model, auto_show=False, constraints=None, preferences=None):
    save_dir = "__CQ_SAVE_DIR__"
    ctx = "__CQ_NAME__"
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        # Merge the constraints/preferences passed to synthesize() into the
        # model (via classiq's set_constraints / set_preferences) so write_qmod
        # sees them.
        if constraints is not None or preferences is not None:
            if not isinstance(model, str):
                model = _cq.create_model(model)
            if preferences is not None:
                model = _cq_syn.set_preferences(model, preferences=preferences)
            if constraints is not None:
                model = _cq_syn.set_constraints(model, constraints=constraints)
        # If a notebook calls synthesize() more than once, each call overwrites
        # the same file — only the last model is kept.
        # write_qmod's symbolic mode requires Qmod-native types throughout; for
        # models with Python-typed classical args (e.g. list[bool]), fall back
        # to the expanded form.
        try:
            write_qmod(model, name=ctx, directory=Path(save_dir), symbolic_only=True, decimal_precision=15)
        except Exception:
            write_qmod(model, name=ctx, directory=Path(save_dir), symbolic_only=False, decimal_precision=15)
        # Replace the sidecar with a minimal version containing only the
        # fields the notebook actually customized.  Pulling from `model`
        # (the serialized JSON) avoids a filesystem round trip; the
        # QFunc + no-kwargs path has no customizations, so the sidecar is {}.
        if isinstance(model, str):
            parsed = _json.loads(model)
            c = parsed.get("constraints") or {}
            p = parsed.get("preferences") or {}
            p.pop("random_seed", None)
        else:
            c, p = {}, {}
        cleaned = {}
        if (s := _strip_defaults(c, _DEFAULT_CONSTRAINTS)):
            cleaned["constraints"] = s
        if (s := _strip_defaults(p, _DEFAULT_PREFERENCES)):
            cleaned["preferences"] = s
        (Path(save_dir) / (ctx + ".synthesis_options.json")).write_text(
            _json.dumps(cleaned, indent=2, sort_keys=True) + "\\n"
        )

    return MagicMock(name="QuantumProgram")

async def _patched_synthesize_async(model, **kw):
    return _patched_synthesize(model, **kw)

_cq.synthesize            = _patched_synthesize
_cq_syn.synthesize        = _patched_synthesize
_cq.synthesize_async      = _patched_synthesize_async
_cq_syn.synthesize_async  = _patched_synthesize_async
_cq.execute               = lambda *a, **kw: MagicMock(name="ExecutionJob")
_cq.execute_async         = lambda *a, **kw: MagicMock(name="ExecutionJob")
_cq.show                  = lambda *a, **kw: None
_cq_syn.show              = lambda *a, **kw: None
# ============================================================
"""

DEFAULT_DIRS = ["algorithms", "applications"]


def make_patch(save_dir: str, name: str) -> str:
    """Return patch code with save_dir and name baked in as literals."""
    return PATCH.replace("__CQ_SAVE_DIR__", save_dir).replace("__CQ_NAME__", name)


def run_notebook(nb_path: Path, save_dir: str, name: str | None = None) -> list[str]:
    """
    Execute a notebook cell-by-cell in its own kernel.
    Returns a list of cell-error strings (empty = clean run).
    name overrides the stem used for output filenames (defaults to nb_path.stem).
    """
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    nb = nbformat.read(nb_path, as_version=4)
    # Override whatever kernel the notebook specifies so notebooks that name a
    # non-existent kernel (e.g. "prod", "prod_py3.11") still run in the current
    # Python environment.
    nb.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    nb.cells.insert(
        0, nbformat.v4.new_code_cell(make_patch(save_dir, name or nb_path.stem))
    )

    errors = []
    client = NotebookClient(nb, timeout=120)
    with client.setup_kernel():
        for idx, cell in enumerate(nb.cells):
            try:
                client.execute_cell(cell, cell_index=idx)
            except CellExecutionError as e:
                first = e.evalue.splitlines()[0] if e.evalue.strip() else "(no message)"
                errors.append(f"  [cell {idx}] {e.ename}: {first}")
    return errors


def run_python(py_path: Path, save_dir: str, tmpdir: str) -> list[str]:
    """Prepend patch to a Python script and run it in a subprocess."""
    patched = Path(tmpdir) / f"_patched_{py_path.stem}.py"
    patched.write_text(make_patch(save_dir, py_path.stem) + "\n" + py_path.read_text())
    subprocess.run([sys.executable, str(patched)])
    return []


def is_handwritten_qmod(path: Path) -> bool:
    """Return True if path exists and contains an inline // comment."""
    return path.exists() and "//" in path.read_text()


def process(
    target: Path, tmpdir: str, index: int, total: int, lock: threading.Lock, force: bool
) -> tuple[Path, bool, str | None, bool]:
    """Run one notebook/script; return (path, qmod_written, fatal_error, skipped)."""
    save_dir = str(target.parent)
    prefix = f"[{index:>{len(str(total))}}/{total}]"
    with lock:
        print(f"{prefix} {target} ...", flush=True)

    # Only process notebooks that have a matching <stem>.metadata.json — that
    # file is the marker for a canonical, library-managed notebook.  Notebooks
    # without one (e.g. .ipynb_checkpoints, community notebooks that manage
    # their own qmod via write_qmod()) are intentionally skipped.
    if target.suffix == ".ipynb":
        metadata_path = Path(save_dir) / f"{target.stem}.metadata.json"
        if not metadata_path.exists():
            with lock:
                print(f"  ~ {target.stem}: skipped (no metadata.json)", flush=True)
            return target, False, None, True

    # Skip hand-written .qmod files unless --force is set.
    # A .qmod is considered hand-written when it contains inline // comments,
    # which write_qmod() never produces.
    qmod_path = Path(save_dir) / f"{target.stem}.qmod"
    if not force and is_handwritten_qmod(qmod_path):
        with lock:
            print(
                f"  ~ {target.stem}: skipped (hand-written .qmod, use --force to override)",
                flush=True,
            )
        return target, False, None, True

    try:
        start = time.time()
        if target.suffix == ".ipynb":
            run_notebook(target, save_dir)
        else:
            run_python(target, save_dir, tmpdir)
        qmod_path = Path(save_dir) / f"{target.stem}.qmod"
        qmod_written = qmod_path.exists() and qmod_path.stat().st_mtime >= start
        # Run the repo's pinned prettier on the JSON sidecar so its layout
        # (short arrays inline, etc.) matches the repo's pre-commit hook.
        # Best-effort: if pre-commit isn't available, the file is still valid
        # JSON, just possibly verbose enough to trigger lint at commit time.
        sidecar = Path(save_dir) / f"{target.stem}.synthesis_options.json"
        if sidecar.exists() and sidecar.stat().st_mtime >= start:
            subprocess.run(
                ["pre-commit", "run", "prettier", "--files", str(sidecar)],
                capture_output=True,
                check=False,
            )
        return target, qmod_written, None, False
    except Exception as e:
        return target, False, f"{type(e).__name__}: {e}", False


def collect_targets(paths: list[str]) -> list[Path]:
    targets: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            # Only collect notebooks from directories — .py files are never
            # auto-discovered because a directory may contain library code,
            # utilities, and test files that are not Classiq synthesis scripts.
            targets += sorted(path.rglob("*.ipynb"))
        elif path.suffix in (".ipynb", ".py"):
            targets.append(path)
        else:
            # treat as a glob or partial name — search under current directory
            matches = sorted(glob.glob(f"**/{p}/**/*.ipynb", recursive=True))
            matches += sorted(glob.glob(f"**/{p}/**/*.py", recursive=True))
            matches += sorted(glob.glob(f"**/{p}*.ipynb", recursive=True))
            matches += sorted(glob.glob(f"**/{p}*.py", recursive=True))
            matches += sorted(glob.glob(p, recursive=True))  # exact glob fallback
            targets += [
                Path(f) for f in dict.fromkeys(matches)
            ]  # preserve order, dedupe
    # dedupe across all entries while preserving order
    seen: set[Path] = set()
    result = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Notebooks (.ipynb), Python scripts (.py), or directories to scan. "
        "Partial directory names (e.g. 'cfd', 'qlbm') are also accepted — "
        "the script will search for matching sub-paths under the current directory. "
        f"Default: {DEFAULT_DIRS}",
    )
    parser.add_argument(
        "--from-file",
        metavar="FILE",
        help="Path to a text file listing entries to process, one per line "
        "(same format as positional arguments: directories, partial names, or file paths). "
        "Blank lines and lines starting with '#' are ignored.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count(),
        help="Number of notebooks to run in parallel (default: number of CPU cores)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite hand-written .qmod files (identified by inline // comments). "
        "By default such files are left untouched.",
    )
    args = parser.parse_args()

    raw_paths = list(args.paths)
    if args.from_file:
        lines = Path(args.from_file).read_text().splitlines()
        raw_paths += [
            line.strip() for line in lines if line.strip() and not line.startswith("#")
        ]

    targets = collect_targets(raw_paths or DEFAULT_DIRS)
    if not targets:
        print("No notebooks or Python files found.")
        sys.exit(1)

    print(f"Files to process : {len(targets)}")
    print(f"Parallel workers : {args.workers}")

    lock = threading.Lock()
    fatal_errors = []
    total_written = 0
    total_skipped = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        futures = {}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for i, t in enumerate(targets, 1):
                fut = pool.submit(process, t, tmpdir, i, len(targets), lock, args.force)
                futures[fut] = t

            for fut in as_completed(futures):
                path, qmod_written, fatal, skipped = fut.result()
                if skipped:
                    total_skipped += 1
                else:
                    if qmod_written:
                        total_written += 1
                    with lock:
                        if fatal:
                            print(f"  ✗ {path.stem}: {fatal}", flush=True)
                            fatal_errors.append((path, fatal))
                        else:
                            print(
                                f"  {'✓' if qmod_written else '○'} {path.stem}",
                                flush=True,
                            )

    print(f"\nDone — {total_written} .qmod file(s) written next to their source files")
    if total_skipped:
        print(f"{total_skipped} notebook(s) skipped")
    if fatal_errors:
        print(f"{len(fatal_errors)} notebook(s) had fatal errors:")
        for p, e in fatal_errors:
            print(f"  {p}: {e}")


if __name__ == "__main__":
    main()
