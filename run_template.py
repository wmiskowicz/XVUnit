from internals.python.xvunit import XVunit
from internals.python.paths import PROJECT_DIR
import os
import sys

xvunit = XVunit()



sources = {
    "rtl": [
        os.path.join(PROJECT_DIR, 'rtl', "timer", "*.sv"),
        # os.path.join(PROJECT_DIR, 'rtl', "*", "*.sv"),
        # os.path.join(PROJECT_DIR, 'rtl', "top_vga", "*.sv"),
        os.path.join(PROJECT_DIR, 'rtl', "z_game_setup", "game_pkg.sv")
    ],
    "sim": [
        os.path.join(PROJECT_DIR, "sim", "timer", "*.sv"),
        os.path.join(PROJECT_DIR, "XVUnit", "internals", "verilog", "*.sv"),
    ],
}



xvunit.set_parameters(
    sources=sources
)


xvunit.run(argv=sys.argv)