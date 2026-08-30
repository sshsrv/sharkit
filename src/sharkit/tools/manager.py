from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from sharkit.tools.base import ToolInstallSpec


class ToolManager:
    def __init__(self, tools_root: Path | None = None) -> None:
        if tools_root is None:
            tools_root = Path.home() / ".local" / "share" / "sharkit" / "tools"
        self._root = tools_root

    @property
    def root(self) -> Path:
        return self._root

    def install_path(self, name: str) -> Path:
        return self._root / name

    def is_installed(self, name: str) -> bool:
        return (self.install_path(name) / ".installed").exists()

    def install(
        self, name: str, spec: ToolInstallSpec, on_progress: Any = None
    ) -> tuple[bool, str]:
        dest = self.install_path(name)
        repo_dir = dest / "repo"
        venv_dir = dest / "venv"
        try:
            dest.mkdir(parents=True, exist_ok=True)
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            if on_progress:
                on_progress("cloning repository...")
            self._run(["git", "clone", "--depth", "1", spec.git_url, str(repo_dir)])
            if spec.venv:
                if on_progress:
                    on_progress("creating virtual environment...")
                self._run([sys.executable, "-m", "venv", str(venv_dir)])
                pip = str(venv_dir / "bin" / "pip")
                if spec.requirements_file:
                    req = repo_dir / spec.requirements_file
                    if on_progress:
                        on_progress(f"installing requirements ({spec.requirements_file})...")
                    self._run([pip, "install", "-r", str(req)])
                if spec.pip_args:
                    if on_progress:
                        on_progress("installing additional packages...")
                    self._run([pip, "install", *spec.pip_args])
            dest.joinpath(".installed").write_text(name)
            return True, f'Tool "{name}" installed.'
        except Exception as e:
            return False, f'Failed to install "{name}": {e}'

    def update(
        self, name: str, spec: ToolInstallSpec, on_progress: Any = None
    ) -> tuple[bool, str]:
        dest = self.install_path(name)
        repo_dir = dest / "repo"
        venv_dir = dest / "venv"
        if not self.is_installed(name):
            return False, f'Tool "{name}" is not installed.'
        try:
            if repo_dir.exists():
                if on_progress:
                    on_progress("pulling latest changes...")
                self._run(["git", "-C", str(repo_dir), "pull", "--ff-only"])
            if spec.venv and venv_dir.exists():
                pip = str(venv_dir / "bin" / "pip")
                if spec.requirements_file:
                    req = repo_dir / spec.requirements_file
                    if on_progress:
                        on_progress("upgrading requirements...")
                    self._run([pip, "install", "--upgrade", "-r", str(req)])
                if spec.pip_args:
                    if on_progress:
                        on_progress("upgrading packages...")
                    self._run([pip, "install", "--upgrade", *spec.pip_args])
            return True, f'Tool "{name}" updated.'
        except Exception as e:
            return False, f'Failed to update "{name}": {e}'

    def uninstall(self, name: str) -> tuple[bool, str]:
        dest = self.install_path(name)
        if not dest.exists():
            return False, f'Tool "{name}" is not installed.'
        try:
            shutil.rmtree(dest)
            return True, f'Tool "{name}" uninstalled.'
        except Exception as e:
            return False, f'Failed to uninstall "{name}": {e}'

    def _run(self, cmd: list[str]) -> None:
        subprocess.run(cmd, check=True, capture_output=True)
