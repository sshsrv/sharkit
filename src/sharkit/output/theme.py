from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOR = _supports_color()

PINK: str = "\033[38;5;205m" if _COLOR else ""
WHITE: str = "\033[38;5;255m" if _COLOR else ""
GRAY: str = "\033[38;5;245m" if _COLOR else ""
GREEN: str = "\033[38;5;114m" if _COLOR else ""
YELLOW: str = "\033[38;5;229m" if _COLOR else ""
RED: str = "\033[38;5;203m" if _COLOR else ""
BLUE: str = "\033[38;5;39m" if _COLOR else ""
RESET: str = "\033[0m" if _COLOR else ""
BOLD: str = "\033[1m" if _COLOR else ""
DIM: str = "\033[2m" if _COLOR else ""


def hex_to_ansi(hex_color: str) -> str:
    if not _COLOR:
        return ""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) < 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
