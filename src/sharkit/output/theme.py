PINK: str = "\033[38;5;205m"
WHITE: str = "\033[38;5;255m"
GRAY: str = "\033[38;5;245m"
GREEN: str = "\033[38;5;114m"
YELLOW: str = "\033[38;5;229m"
RED: str = "\033[38;5;203m"
BLUE: str = "\033[38;5;39m"
RESET: str = "\033[0m"
BOLD: str = "\033[1m"
DIM: str = "\033[2m"


def hex_to_ansi(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"
