# Runs the counter example straight from a clone of the XVunit repository:
#
#   python examples/counter/run.py           # run all test cases
#   python examples/counter/run.py -l        # list test cases
#   python examples/counter/run.py counter_tb.counts_up
#
# In your own project, start from run_template.py instead.
import os
import sys

HERE      = os.path.dirname(os.path.abspath(__file__))
XVUNIT    = os.path.abspath(os.path.join(HERE, ".."))

# Keep build output next to this example instead of above the repository
os.environ.setdefault("XVUNIT_BUILD_DIR", os.path.join(HERE, "xvunit_out"))
sys.path.insert(0, os.path.join(XVUNIT, "internals", "python"))

from xvunit import XVunit

sources = {
    "rtl": [
        os.path.join(HERE, "counter.sv"),
    ],
    "sim": [
        os.path.join(HERE, "counter_tb.sv"),
        os.path.join(XVUNIT, "internals", "verilog", "*.sv"),
    ],
}

xvunit = XVunit()
xvunit.set_parameters(sources=sources)
xvunit.run(argv=sys.argv)
