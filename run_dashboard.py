"""Entry point to run the Streamlit dashboard from the project root."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
app_path = PROJECT_ROOT / "dashboard" / "app.py"

if __name__ == "__main__":
    sys.exit(
        subprocess.call(
            [sys.executable, "-m", "streamlit", "run", str(app_path), *sys.argv[1:]],
            cwd=PROJECT_ROOT,
        )
    )
