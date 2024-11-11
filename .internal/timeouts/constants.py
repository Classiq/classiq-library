import subprocess
from pathlib import Path

Seconds = float

DEFAULT_TIMEOUT_IPYNB: Seconds = 20
DEFAULT_TIMEOUT_QMOD: Seconds = 10

ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605
TIMEOUTS_FILE = "timeouts.yaml"
TIMEOUTS_PATH = ROOT / "tests" / "resources" / TIMEOUTS_FILE
