from __future__ import annotations

import contextlib
import fcntl
import os
import pty
import re
import select
import struct
import subprocess
import termios
from dataclasses import replace

from sharkit.output.theme import PINK, hex_to_ansi
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolInstallSpec,
    ToolMetadata,
    parse_bool,
)

_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
_OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", re.DOTALL)


def _clean_ansi(text: str) -> str:
    text = _OSC_RE.sub("", text)
    return _CSI_RE.sub(lambda m: m.group(0) if m.group(0).endswith("m") else "", text)


class BlackbirdTool(Tool):
    metadata = ToolMetadata(
        name="blackbird",
        description="Blackbird multi-source OSINT aggregation tool",
        category="recon",
        author="p1ngul1n0",
        version="0.1.0",
        safety="safe",
        color="#D0021B",
        install=ToolInstallSpec(
            git_url="https://github.com/p1ngul1n0/blackbird.git",
            requirements_file="requirements.txt",
            entry="blackbird.py",
        ),
    )

    def __init__(self) -> None:
        self._options = {
            "type": OptionDefinition(
                name="type",
                description="Search type: username or email",
                required=True,
                choices=["username", "email"],
            ),
            "query": OptionDefinition(
                name="query",
                description="Target to search (username or email)",
                required=True,
            ),
            "pdf": OptionDefinition(
                name="pdf",
                description="Export results to PDF",
                required=False,
                default=None,
                type="bool",
            ),
        }

    def get_metadata(self) -> ToolMetadata:
        return self.metadata

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

    def set_option(self, key: str, value: str) -> None:
        if key not in self._options:
            raise ValueError(f'Option "{key}" not found.')
        self._options[key] = replace(self._options[key], value=value)

    def execute(self, context: ExecutionContext) -> Result:
        from sharkit.tools.manager import ToolManager

        name = self.metadata.name
        tool_color = hex_to_ansi(self.metadata.color) if self.metadata.color else PINK
        manager = ToolManager()
        if not manager.is_installed(name):
            return Result(
                success=False,
                error=f'Tool "{name}" is not installed. Run: install {name}',
            )
        spec = self.metadata.install
        if spec is None:
            return Result(success=False, error="Tool has no install spec.")
        install_dir = manager.install_path(name)
        repo_dir = install_dir / "repo"
        venv_python = install_dir / "venv" / "bin" / "python"
        script = repo_dir / (spec.entry or "blackbird.py")
        if not script.exists():
            return Result(success=False, error=f"Entry script not found: {script}")
        stype = context.options.get("type") or ""
        query = context.options.get("query") or ""
        if not stype or not query:
            return Result(
                success=False,
                error="Both 'type' and 'query' options are required.",
            )
        args = [f"--{stype}", query, "--no-update"]
        if parse_bool(context.options.get("pdf")):
            args.append("--pdf")
        renderer = context.renderer
        master, slave = pty.openpty()
        try:
            winsize = struct.pack("HHHH", 1000, 10000, 0, 0)
            fcntl.ioctl(master, termios.TIOCSWINSZ, winsize)
            attrs = termios.tcgetattr(master)
            attrs[1] &= ~termios.OPOST
            termios.tcsetattr(master, termios.TCSANOW, attrs)
        except OSError:
            pass
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["FORCE_COLOR"] = "1"
        env["CLICOLOR"] = "1"
        env["CLICOLOR_FORCE"] = "1"
        env["COLUMNS"] = "10000"
        try:
            proc = subprocess.Popen(
                [str(venv_python), str(script), *args],
                stdout=slave,
                stderr=slave,
                stdin=subprocess.DEVNULL,
                cwd=str(repo_dir),
                env=env,
                start_new_session=True,
            )
        except Exception as e:
            return Result(success=False, error=f"Failed to run {name}: {e}")
        finally:
            with contextlib.suppress(OSError):
                os.close(slave)
        first = True
        current = ""
        started = False
        pending_blank = False
        try:
            while True:
                try:
                    r, _, _ = select.select([master], [], [], 0.5)
                except (OSError, ValueError):
                    break
                if not r:
                    if proc.poll() is not None:
                        break
                    continue
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                if not started:
                    chunk = chunk.lstrip(b"\n")
                    started = True
                for ch in chunk.decode("utf-8", errors="replace"):
                    if ch == "\n":
                        if current:
                            if pending_blank:
                                if renderer is not None:
                                    renderer.gutter(name, "", tool_color, False)
                                else:
                                    print()
                                pending_blank = False
                            if renderer is not None:
                                renderer.gutter(name, _clean_ansi(current), tool_color, first)
                            else:
                                print(_clean_ansi(current))
                            first = False
                        else:
                            pending_blank = True
                        current = ""
                    elif ch == "\r":
                        current = ""
                    else:
                        current += ch
        except KeyboardInterrupt:
            # Catch Ctrl+C so a run aborts cleanly and the framework keeps running.
            with contextlib.suppress(OSError):
                proc.kill()
            current = ""
            if renderer is not None:
                # \r\033[K clears the ^C echo from the terminal before printing.
                print("\r\033[K", end="")
                renderer.gutter(name, "Run aborted (Ctrl+C).", tool_color, first)
            else:
                print("Run aborted (Ctrl+C).")
            return Result(success=True, data={})
        finally:
            if current:
                if renderer is not None:
                    renderer.gutter(name, _clean_ansi(current), tool_color, first)
                else:
                    print(_clean_ansi(current))
            with contextlib.suppress(OSError):
                os.close(master)
            with contextlib.suppress(OSError):
                proc.wait()
        return Result(success=True, data={})
