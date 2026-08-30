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

from sharkit.output.theme import PINK, hex_to_ansi
from sharkit.tools.base import (
    ExecutionContext,
    OptionDefinition,
    Result,
    Tool,
    ToolInstallSpec,
    ToolMetadata,
)

_CSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
_OSC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", re.DOTALL)


def _clean_ansi(text: str) -> str:
    text = _OSC_RE.sub("", text)
    return _CSI_RE.sub(lambda m: m.group(0) if m.group(0).endswith("m") else "", text)


class SocialAnalyzerTool(Tool):
    metadata = ToolMetadata(
        name="social-analyzer",
        description="Social Analyzer — find profiles across 400+ social networks",
        category="recon",
        author="qeeqbox",
        version="0.1.0",
        safety="safe",
        color="#8E44AD",
        install=ToolInstallSpec(
            git_url="https://github.com/qeeqbox/social-analyzer.git",
            pip_args=["social-analyzer"],
        ),
    )

    def __init__(self) -> None:
        self._options = {
            "username": OptionDefinition(
                name="username",
                description="Target username to search",
                required=True,
            ),
            "timeout": OptionDefinition(
                name="timeout",
                description="Timeout per site in seconds",
                required=False,
                default=None,
            ),
        }

    def get_metadata(self) -> ToolMetadata:
        return self.metadata

    def get_options(self) -> dict[str, OptionDefinition]:
        return self._options

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
        social_analyzer_bin = install_dir / "venv" / "bin" / "social-analyzer"
        if not social_analyzer_bin.exists():
            return Result(
                success=False,
                error=f"social-analyzer binary not found: {social_analyzer_bin}",
            )

        username = context.options.get("username") or ""
        if not username:
            return Result(success=False, error="Option 'username' is required.")

        args = ["--username", username]
        timeout = context.options.get("timeout")
        if timeout:
            args.extend(["--timeout", str(timeout)])

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
                [str(social_analyzer_bin), *args],
                stdout=slave,
                stderr=slave,
                stdin=subprocess.DEVNULL,
                cwd=str(install_dir),
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
                                renderer.gutter(
                                    name, _clean_ansi(current), tool_color, first
                                )
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
            with contextlib.suppress(OSError):
                proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(OSError):
                    proc.kill()
            current = ""
            if renderer is not None:
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
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(OSError):
                    proc.kill()
                proc.wait(timeout=2)

        return Result(success=True, data={})
