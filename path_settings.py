import glob
import os
import shutil
import sys
from pathlib import Path

# -------------------------------------------------------------------------
# Path setup
# -------------------------------------------------------------------------
# Nothing here needs editing. Override any of these with environment variables:
#
#   XVUNIT_VIVADO_PATH  Vivado install root, e.g. C:\Xilinx\Vivado\2023.1 or
#                       /tools/Xilinx/Vivado/2023.1 (its bin/ folder also works)
#   XVUNIT_BUILD_DIR    Where simulation build output and logs are written
#                       (default: <project>/xvunit_out)
# -------------------------------------------------------------------------
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR     = Path(THIS_SCRIPT_DIR).parent.resolve()
BUILD_DIR       = os.path.abspath(os.environ.get("XVUNIT_BUILD_DIR", os.path.join(PROJECT_DIR, "xvunit_out")))

IS_WINDOWS = sys.platform.startswith("win")

# Default install locations searched when nothing else is configured
_SEARCH_PATTERNS = [
    r"C:\Xilinx\Vivado\*",
    r"C:\AMDDesignTools\*\Vivado",
] if IS_WINDOWS else [
    "/tools/Xilinx/Vivado/*",
    "/opt/Xilinx/Vivado/*",
    "/tools/Xilinx/*/Vivado",
    "/opt/Xilinx/*/Vivado",
    os.path.expanduser("~/Xilinx/Vivado/*"),
]


def _has_xvlog(root):
    exe = "xvlog.bat" if IS_WINDOWS else "xvlog"
    return os.path.isfile(os.path.join(root, "bin", exe))


def find_vivado_root():
    """Return the Vivado install root, or None if it cannot be found.

    Order: XVUNIT_VIVADO_PATH, then xvlog on PATH, then the newest install
    in the default locations.
    """
    
    env_path = os.environ.get("XVUNIT_VIVADO_PATH")
    if env_path:
        root = os.path.abspath(env_path)
        if os.path.basename(root).lower() == "bin":
            root = os.path.dirname(root)
        return root

    xvlog = shutil.which("xvlog")
    if xvlog:
        return str(Path(xvlog).resolve().parent.parent)

    candidates = []
    for pattern in _SEARCH_PATTERNS:
        candidates.extend(p for p in glob.glob(pattern) if _has_xvlog(p))
    return sorted(candidates)[-1] if candidates else None


VIVADO_ROOT = find_vivado_root()
VIVADO_DIR  = os.path.join(VIVADO_ROOT, "bin") if VIVADO_ROOT else None
