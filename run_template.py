# Copy this file to your host project's root directory (next to the XVunit
# folder) and rename it, e.g. run_my_module.py. Then adjust the "sources"
# below to point at your own RTL and testbench files.
import os
import sys

from XVunit.internals.python.xvunit import XVunit
from XVunit.path_settings import PROJECT_DIR

xvunit = XVunit()

sources = {
    "rtl": [
        os.path.join(PROJECT_DIR, "rtl", "my_module", "*.sv"),
    ],
    "sim": [
        os.path.join(PROJECT_DIR, "sim", "my_module", "*.sv"),
        os.path.join(PROJECT_DIR, "XVunit", "internals", "verilog", "*.sv"),
    ],
}

xvunit.set_parameters(
    sources=sources
)

xvunit.run(argv=sys.argv)
