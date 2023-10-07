"""ANSI color codes for terminal output."""

import os
import sys


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if os.name == "nt":
        return bool(os.environ.get("MSYSTEM") or os.environ.get("TERM"))
    return True


_COLOR = _supports_color()


class C:
    HEADER = "\033[95m" if _COLOR else ""
    BLUE   = "\033[94m" if _COLOR else ""
    CYAN   = "\033[96m" if _COLOR else ""
    GREEN  = "\033[92m" if _COLOR else ""
    YELLOW = "\033[93m" if _COLOR else ""
    RED    = "\033[91m" if _COLOR else ""
    BOLD   = "\033[1m"  if _COLOR else ""
    DIM    = "\033[2m"  if _COLOR else ""
    RESET  = "\033[0m"  if _COLOR else ""
