# Third-party licenses

XVunit's own code (everything under `internals/python/`, `path_settings.py`,
`run_template.py`) is licensed under the MIT License — see [`LICENSE`](LICENSE).

## VUnit (Mozilla Public License 2.0)

The following files are adapted from the [VUnit](https://github.com/VUnit/vunit)
project, Copyright (c) 2014-2023 Lars Asplund (lars.anders.asplund@gmail.com),
and remain licensed under the **Mozilla Public License, v. 2.0**, in
accordance with the license header at the top of each file:

- `internals/verilog/xvunit_pkg.sv`
- `internals/verilog/xvunit_defines.svh`

These implement the SystemVerilog `` `TEST_CASE ``/`` `CHECK_EQUAL `` runtime
that XVunit's Python layer drives. They have been renamed from VUnit's
`vunit_pkg`/`vunit_defines.svh` for use alongside XVunit, but the
implementation is in the most part VUnit's.

A copy of the MPL 2.0 is available at <https://www.mozilla.org/en-US/MPL/2.0/>.
Per the MPL, you may use, modify, and redistribute these two files — including
as part of a larger work under a different license, such as XVunit's MIT
license above — provided that any copy of these specific files (modified or
not) that you distribute remains available under the MPL 2.0 with its
original copyright notice intact.

All credit for the test-runner design and macro set in these two files goes
to the VUnit project and its authors: <https://vunit.github.io/>.
