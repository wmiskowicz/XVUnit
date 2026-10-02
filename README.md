# XVunit

XVunit is a small test runner that brings [VUnit](https://vunit.github.io/)-style
unit testing to **AMD/Xilinx Vivado's `xsim` simulator**. It drives `xvlog` /
`xvhdl` / `xelab` / `xsim` directly from the command line with limited support of Vivado GUI (-g),
no manually maintained `.prj` files — and gives you VUnit's familiar
`` `TEST_CASE ``, `` `CHECK_EQUAL `` style macros for SystemVerilog
testbenches, with per-test-case pass/fail reporting and incremental
recompilation.

## Requirements

- AMD Vivado install with the simulator tools (`xvlog`, `xvhdl`,
  `xelab`, `xsim`) on the machine.
- Python 3.8+
- The `colorama` package (`pip install colorama`)

XVunit currently launches Vivado's tools via `VIVADO_SETUP` (a Windows
`settings64.bat`), see [Configuration](#configuration) below.

## Installation

Add XVunit as a git submodule in the root of your HDL project:

```sh
git submodule add https://github.com/wmiskowicz/XVunit.git XVunit
```

The folder **must** be named `XVunit` (matching case) — the tool resolves
its own bundled SystemVerilog sources relative to this folder name, and
several path checks are case-sensitive on Linux/macOS.

## Quick start

1. Adjust your Vivado path in [`path_settings.py`](path_settings.py)
2. Copy [`run_template.py`](run_template.py) into your project's root
   directory and rename it, e.g. `run_my_module.py`.
3. Point the `sources` dictionary at your own RTL and testbench files.
   Glob patterns (`*`) are expanded; plain paths are used as-is. Always
   include XVunit's own runtime package so your testbenches can use the
   `` `TEST_CASE ``/`` `CHECK_EQUAL `` macros:

   ```python
   sources = {
       "rtl": [
           os.path.join(PROJECT_DIR, "rtl", "my_module", "*.sv"),
       ],
       "sim": [
           os.path.join(PROJECT_DIR, "sim", "my_module", "*.sv"),
           os.path.join(PROJECT_DIR, "XVunit", "internals", "verilog", "*.sv"),
       ],
   }
   ```
4. Run it:

   ```sh
   python run_my_module.py        # run every discovered testbench
   python run_my_module.py -l     # list discovered testbenches/test cases
   python run_my_module.py my_module_tb           # run one testbench
   python run_my_module.py my_module_tb.TC000      # run one test case
   python run_my_module.py my_module_tb.TC000 -g   # open in the xsim GUI
   python run_my_module.py my_module_tb -v         # verbose xsim output
   ```

A testbench is only picked up if it both contains `` `TEST_CASE `` and
includes `xvunit_defines.svh`.

## Writing a testbench

```systemverilog
`include "xvunit_defines.svh"

module my_module_tb;
  `TEST_SUITE_BEGIN

    `TEST_CASE("resets_to_zero")
      // ... drive DUT, then:
      `CHECK_EQUAL(dut.counter, 0);

    `TEST_CASE("counts_up")
      `CHECK_EQUAL(dut.counter, 1);

  `TEST_SUITE_END
endmodule
```

See `internals/verilog/xvunit_defines.svh` for the full macro set
(`CHECK_EQUAL`, `CHECK_NOT_EQUAL`, `CHECK_GREATER`, `CHECK_LESS`,
`CHECK_EQUAL_VARIANCE`, `WATCHDOG`, setup/cleanup hooks, ...).

## Configuration

All machine-specific paths live in [`path_settings.py`](path_settings.py):

| Variable       | Meaning                                                   |
|----------------|------------------------------------------------------------|
| `PROJECT_DIR`  | Root of the host project (one level above the `XVunit/` folder) |
| `BUILD_DIR`    | `<PROJECT_DIR>/xvunit_out` — simulation build output and logs |
| `VIVADO_DIR`   | Vivado's `bin` directory |
| `VIVADO_SETUP` | Path to Vivado's `settings64.bat` (sourced before every tool invocation) |

Edit these to match your Vivado install location.


## CLI reference

| Flag | Description |
|------|-------------|
| `-l`, `--list` | List all discovered testbenches and test cases |
| `-t`, `--test` | Run a specific testbench or `testbench.test_case` (supports `fnmatch` wildcards) |
| `-g`, `--gui`  | Open the simulation in the `xsim` GUI (use with `-t`) |
| `-v`           | Verbose: stream raw `xsim`/`xvlog`/`xelab` output |
| `-h`           | Print help |
| *(no flags)*   | Run every discovered testbench |

## Project layout

```
XVunit/
├── path_settings.py           # Vivado install paths, build dir (edit per machine)
├── run_template.py            # copy this out to your project root
├── internals/
│   ├── python/                 # the runner itself
│   │   ├── xvunit.py            # public entry point (XVunit class)
│   │   ├── parser.py            # xsim.log tailing, pass/fail + progress reporting
│   │   ├── test_bench.py        # testbench/test-case discovery
│   │   ├── file_manager.py      # .prj file generation
│   │   └── logger.py            # summary printing
│   └── verilog/                 # SystemVerilog test macros (from VUnit, see License)
│       ├── xvunit_defines.svh
│       └── xvunit_pkg.sv
└── README.md
```

## Known limitations

- Vivado tool invocation currently assumes a Windows `settings64.bat`
  (`VIVADO_SETUP`). Linux users will need to adapt `XVUnitRunner.setup_cmd`
  in `internals/python/xvunit_runner.py` to source Vivado's `settings64.sh`
  instead.
- The Python process's exit code reflects whether compilation/elaboration/
  simulation *launched* successfully, not whether every test case inside
  passed — check the printed summary (or the per-test-case `.log` files
  under `sim/xvunit_out/`) for actual pass/fail status.

## License

XVunit's own code (everything under `internals/python/`, `path_settings.py`,
`run_template.py`) is licensed under the [MIT License](LICENSE).

`internals/verilog/xvunit_pkg.sv` and `internals/verilog/xvunit_defines.svh`
are adapted from the [VUnit](https://github.com/VUnit/vunit) project
(Copyright © Lars Asplund) and remain licensed under the **Mozilla Public
License 2.0**, per their file headers. See
[`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) for details. All
credit for the underlying test-runner design and macro set goes to the
VUnit project — XVunit only ports the pieces needed to drive Vivado's
`xsim` directly.
