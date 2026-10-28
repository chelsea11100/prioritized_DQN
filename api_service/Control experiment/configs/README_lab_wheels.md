# Lab offline SMAC3 wheels

The directories `_wheels_smac3/` and `_wheels_smac3_linux/` are **not** in git (size + platform-specific).

When the lab cannot reach PyPI, upload Linux cp310 wheels to the server under:

`Control experiment/configs/_wheels_smac3_linux/`

Then run `smac3_fill_e3_lab.py` on the lab host (see `run_minimal_journal_suite.sh` and related scripts in this folder).
