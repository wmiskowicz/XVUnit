import os
from pathlib import Path

# -------------------------------------------------------------------------
# Path setup
# -------------------------------------------------------------------------
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR     = Path(THIS_SCRIPT_DIR).parent.parent.parent.resolve()
SIM_DIR         = os.path.join(PROJECT_DIR, "sim")
BUILD_DIR       = os.path.join(SIM_DIR, "build")
XSIM_LOG        = os.path.join(BUILD_DIR, "xsim.log")

VIVADO_DIR=r"C:\Xilinx\Vivado\2023.1\bin"
VIVADO_SETUP=r"C:\Xilinx\Vivado\2023.1\settings64.bat"