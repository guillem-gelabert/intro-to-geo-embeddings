"""Wrapper test invoking tools/verify_slides.py so `make test` covers the deck set.

Plan 07-05: the structural checker itself is a standalone script (matching
tools/derive_exercise.py's CLI convention), invoked here via subprocess so a
plain `uv run pytest tests/` run surfaces any deck regression.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_verify_slides_passes():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "verify_slides.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"verify_slides.py failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "PASS:" in result.stdout
