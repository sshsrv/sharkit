import re
import shutil
import textwrap

from sharkit import __version__
from sharkit.output.theme import (
    BOLD,
    DIM,
    GRAY,
    PINK,
    RESET,
    WHITE,
)

ANSI_RE = re.compile(r"\033\[[0-9;]*m")

BANNER_ART = r'''   .x+=:.                                              ..         .         s
  z`    ^%    .uef^"                             < .z@8"`        @88>      :8
     .   <k :d88E                      .u    .    !@88E          %8P      .88
   .@8Ned8" `888E             u      .d88B :@8c   '888E   u       .      :888ooo
 .@^%8888"   888E .z8k     us888u.  ="8888f8888r   888E u@8NL   .@88u  -*8888888
x88:  `)8b.  888E~?888L .@88 "8888"   4888>'88"    888E`"88*"  ''888E`   8888
8888N=*8888  888E  888E 9888  9888    4888> '      888E .dN.     888E    8888
 %8"    R88  888E  888E 9888  9888    4888>        888E~8888     888E    8888
  @8Wou 9%   888E  888E 9888  9888   .d888L .+     888E '888&    888E   .8888Lu=
.888888P`    888E  888E 9888  9888   ^"8888*"      888E  9888.   888&   ^%888*
`   ^"F     m888N= 888> "888*""888"     "Y"      '"888*" 4888"   R888"    'Y"
             `Y"   888   ^Y"   ^Y'                  ""    ""      ""
                  J88"
                  @%
                :"'''


def _visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _visible_len(text))


def _center(text: str, width: int) -> str:
    vis = _visible_len(text)
    if vis >= width:
        return text
    total = width - vis
    left = total // 2
    return " " * left + text + " " * (total - left)


def _term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


class Renderer:
    def panel(
        self,
        title: str,
        content: str,
        min_width: int = 0,
        centered: bool = False,
        wrap: bool = False,
        wrap_width: int = 72,
    ) -> None:
        if wrap:
            wrapped: list[str] = []
            for para in content.splitlines():
                if para.strip() == "":
                    wrapped.append("")
                else:
                    wrapped.extend(textwrap.wrap(para, wrap_width) or [""])
            lines = wrapped
        else:
            lines = content.splitlines()
        content_width = max((_visible_len(line) for line in lines), default=0)
        title_width = _visible_len(title)
        inner = max(content_width, title_width + 3, min_width)
        box_width = inner + 4

        if centered:
            gap = inner - title_width
            left = gap // 2
            right = gap - left
            top = (
                f"{PINK}╭{'─' * left}{RESET} {BOLD}{WHITE}{title}{RESET}"
                f"{PINK} {'─' * right}╮{RESET}"
            )
        else:
            dashes = max(0, inner - title_width - 1)
            top = f"{PINK}╭─ {BOLD}{WHITE}{title}{RESET}{PINK} {'─' * dashes}╮{RESET}"
        if centered:
            body = [f"{PINK}│{RESET} {_center(line, inner)} {PINK}│{RESET}" for line in lines]
        else:
            body = [f"{PINK}│{RESET} {_pad(line, inner)} {PINK}│{RESET}" for line in lines]
        bottom = f"{PINK}╰{'─' * (inner + 2)}╯{RESET}"

        all_lines = [top, *body, bottom]
        if centered:
            pad = max(0, (_term_width() - box_width) // 2)
            all_lines = [" " * pad + ln for ln in all_lines]
        for ln in all_lines:
            print(ln)

    def info(self, message: str) -> None:
        print(f"{WHITE}{message}{RESET}")

    def success(self, message: str) -> None:
        self.panel("success", message)

    def warning(self, message: str) -> None:
        self.panel("warning", message)

    def error(self, message: str) -> None:
        self.panel("error", message)

    def banner(
        self,
        tool_count: int = 0,
        centered: bool = True,
        message: str | None = None,
    ) -> None:
        if centered:
            self._print_centered_block(BANNER_ART)
            print()
            print(
                self._centered_line(
                    f"{BOLD}{PINK}sharkit{RESET} {DIM}v{__version__}{RESET}"
                    f"{WHITE} • the intelligence framework :3{RESET}"
                )
            )
        else:
            for ln in BANNER_ART.splitlines():
                print(f"{PINK}{ln}{RESET}")
            print()
            print(
                f"{BOLD}{PINK}sharkit{RESET} {DIM}v{__version__}{RESET}"
                f"{WHITE} • the intelligence framework :3{RESET}"
            )
        print()

        if message is not None:
            self.centered_box(message)
            return

        print(self._centered_line(f"{DIM}currently serving {tool_count} tools{RESET}"))
        print()
        disclaimer = (
            "sharkit is intended for lawful OSINT research, authorized security testing, "
            "education, and legitimate investigations. You are responsible for complying "
            "with applicable laws, permissions, and terms of service.\n\n"
            "sharkit does not guarantee anonymity."
        )
        self.panel("disclaimer", disclaimer, centered=True, wrap=True, wrap_width=72)

    def centered_box(self, content: str) -> None:
        lines = content.splitlines()
        content_width = max((_visible_len(line) for line in lines), default=0)
        body_width = content_width + 2
        box_width = body_width + 2
        pad = max(0, (_term_width() - box_width) // 2)
        top = f"{PINK}╭{'─' * body_width}╮{RESET}"
        bottom = f"{PINK}╰{'─' * body_width}╯{RESET}"
        body = [f"{PINK}│{RESET} {_center(line, content_width)} {PINK}│{RESET}" for line in lines]
        for ln in [top, *body, bottom]:
            print(" " * pad + ln)

    def _print_centered_block(self, text: str, color: str = PINK) -> None:
        lines = text.splitlines()
        max_w = max((_visible_len(ln) for ln in lines), default=0)
        pad = max(0, (_term_width() - max_w) // 2)
        for ln in lines:
            print(f"{color}{' ' * pad}{ln}{RESET}")

    def _centered_line(self, text: str) -> str:
        pad = max(0, (_term_width() - _visible_len(text)) // 2)
        return " " * pad + text

    def table(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
        centered: bool = False,
    ) -> None:
        col_count = len(headers)
        col_widths = [0] * col_count
        for i, h in enumerate(headers):
            col_widths[i] = _visible_len(h)
        for row in rows:
            for i in range(col_count):
                cell = row[i] if i < len(row) else ""
                col_widths[i] = max(col_widths[i], _visible_len(cell))

        def fmt_row(cells: list[str]) -> str:
            parts = []
            for i in range(col_count):
                cell = cells[i] if i < len(cells) else ""
                parts.append(_pad(cell, col_widths[i]))
            return "  ".join(parts)

        content_lines = [fmt_row(headers)] + [fmt_row(r) for r in rows]
        content_width = max((_visible_len(line) for line in content_lines), default=0)
        body_width = content_width + 2
        title_width = _visible_len(title)
        box_width = body_width + 2

        if centered:
            gap = body_width - title_width
            left = gap // 2
            right = gap - left
            top = (
                f"{PINK}╭{'─' * left}{RESET} {BOLD}{WHITE}{title}{RESET}"
                f"{PINK} {'─' * right}╮{RESET}"
            )
        else:
            dashes = max(0, body_width - title_width - 3)
            top = f"{PINK}╭─ {BOLD}{WHITE}{title}{RESET}{PINK} {'─' * dashes}╮{RESET}"
        header_cells = [f"{BOLD}{WHITE}{h}{RESET}" for h in headers]
        header_line = f"{PINK}│{RESET} {fmt_row(header_cells)} {PINK}│{RESET}"
        sep = f"{PINK}├{'─' * body_width}┤{RESET}"
        if centered:
            row_lines = [
                f"{PINK}│{RESET} {_center(fmt_row(row), content_width)} {PINK}│{RESET}"
                for row in rows
            ]
        else:
            row_lines = [f"{PINK}│{RESET} {fmt_row(row)} {PINK}│{RESET}" for row in rows]
        bottom = f"{PINK}╰{'─' * body_width}╯{RESET}"

        all_lines = [top, header_line, sep, *row_lines, bottom]
        if centered:
            pad = max(0, (_term_width() - box_width) // 2)
            all_lines = [" " * pad + ln for ln in all_lines]
        for ln in all_lines:
            print(ln)

    def result(self, data: dict[str, object]) -> None:
        lines = [f"{BOLD}{key}{RESET}  {value}" for key, value in data.items()]
        self.panel("result", "\n".join(lines))

    def tool_info(self, metadata: dict[str, str]) -> None:
        lines = [
            f"{GRAY}{key}{RESET}  {BOLD}{value}{RESET}"
            for key, value in metadata.items()
        ]
        self.panel("tool info", "\n".join(lines))

    def raw(self, text: str) -> None:
        print(text, end="")

    def log_line(self, tag: str, message: str, color: str = PINK) -> None:
        print(f"{color}{BOLD}{tag} - {RESET}{message}")

    def gutter(self, name: str, line: str, color: str, is_first: bool) -> None:
        if is_first:
            prefix = f"{RESET}{color}{BOLD}{name}{RESET} {color}{BOLD}│{RESET} "
        else:
            prefix = f"{RESET}{' ' * (len(name) + 1)}{color}{BOLD}│{RESET} "
        print(prefix + line)
