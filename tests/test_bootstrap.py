"""Setup-cell bootstrap contract test (ENV-02).

Proves, via a synthetic in-memory notebook, that the Colab Setup cell
pattern every future notebook copies is correct before any real notebook
exists: the Colab-detection control flow, the course.config contract
(RANDOM_STATE, COURSE_RELEASE), and kernel-to-project-venv resolution.

The Setup cell source below is reproduced verbatim from 01-RESEARCH.md's
"Code Examples" section (Colab Setup cell). The test environment is local,
not Colab, so `IN_COLAB` evaluates False and the pip-install block is
skipped entirely — this test exercises the cell's control flow and its
course.config contract, not a live Colab install (that is a separate,
manual checkpoint owned by plan 01-05).
"""

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

from course.config import KERNEL_NAME

# Verbatim from 01-RESEARCH.md, "Code Examples" > "Colab Setup cell".
SETUP_CELL_SOURCE = """
# %% tags=["setup"]
import importlib.util, subprocess, sys
IN_COLAB = "google.colab" in sys.modules
REQUIRED = {"geopandas": "geopandas", "pyarrow": "pyarrow", "mapclassify": "mapclassify"}
if IN_COLAB:
    missing = [pip for mod, pip in REQUIRED.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

from course.config import RANDOM_STATE, COURSE_RELEASE
import numpy as np
np.random.seed(RANDOM_STATE)
"""

# Appended as a second cell so a CellExecutionError here fails the test
# loudly if RANDOM_STATE/COURSE_RELEASE ever drift, or if the kernel
# resolves something other than this project's own virtual environment.
ASSERTIONS_SOURCE = """
assert not IN_COLAB, "test environment must not report itself as Colab"
assert RANDOM_STATE == 42, f"RANDOM_STATE drifted from course/config.py: {RANDOM_STATE!r}"
assert COURSE_RELEASE == "2026.08", f"COURSE_RELEASE drifted from course/config.py: {COURSE_RELEASE!r}"
assert ".venv" in sys.executable, f"kernel did not resolve a project .venv: {sys.executable!r}"
"""


def test_setup_cell_executes_and_matches_config_contract(write_notebook):
    nb_path = write_notebook([SETUP_CELL_SOURCE, ASSERTIONS_SOURCE])
    nb = nbformat.read(nb_path, as_version=4)

    client = NotebookClient(nb, kernel_name=KERNEL_NAME, timeout=60)
    try:
        client.execute()
    except CellExecutionError as exc:
        raise AssertionError(
            f"Setup cell failed to execute cleanly against kernel "
            f"{KERNEL_NAME!r}: {exc}"
        ) from exc
