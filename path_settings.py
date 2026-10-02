import os
from pathlib import Path

# -------------------------------------------------------------------------
# Path setup
# -------------------------------------------------------------------------
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR     = Path(THIS_SCRIPT_DIR).parent.resolve()
BUILD_DIR       = os.path.join(PROJECT_DIR, "xvunit_out")

VIVADO_DIR=r"C:\Xilinx\Vivado\2023.1\bin"
VIVADO_SETUP=r"C:\Xilinx\Vivado\2023.1\settings64.bat"
