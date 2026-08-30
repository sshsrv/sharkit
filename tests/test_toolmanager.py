from dataclasses import dataclass

from sharkit.commands.base import CommandContext
from sharkit.commands.builtins import InstallCommand, RemoveCommand, UpgradeCommand, UseCommand
from sharkit.tools.base import Tool, ToolInstallSpec, ToolMetadata
from sharkit.tools.manager import ToolManager
from sharkit.tools.registry import ToolRegistry


@dataclass
class _FakeResult:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


def test_is_installed_false_when_absent(tmp_path):
    mgr = ToolManager(tools_root=tmp_path / "tools")
    assert mgr.is_installed("x") is False


def test_install_writes_marker_and_is_installed(tmp_path, monkeypatch):
    mgr = ToolManager(tools_root=tmp_path / "tools")
    monkeypatch.setattr(
        "sharkit.tools.manager.subprocess.run",
        lambda *a, **k: _FakeResult(),
    )
    spec = ToolInstallSpec(
        git_url="https://example.com/x.git",
        requirements_file="requirements.txt",
    )
    ok, msg = mgr.install("x", spec)
    assert ok is True
    assert mgr.is_installed("x") is True
    assert (mgr.install_path("x") / ".installed").exists()


def test_uninstall_removes_marker(tmp_path, monkeypatch):
    mgr = ToolManager(tools_root=tmp_path / "tools")
    monkeypatch.setattr(
        "sharkit.tools.manager.subprocess.run",
        lambda *a, **k: _FakeResult(),
    )
    spec = ToolInstallSpec(git_url="https://example.com/x.git")
    mgr.install("x", spec)
    ok, msg = mgr.uninstall("x")
    assert ok is True
    assert mgr.is_installed("x") is False


class _FakeManager:
    def __init__(self) -> None:
        self.installed: set[str] = set()
        self.log: list[tuple[str, str]] = []

    def is_installed(self, name: str) -> bool:
        return name in self.installed

    def install(self, name: str, spec: ToolInstallSpec, on_progress=None) -> tuple[bool, str]:
        self.installed.add(name)
        self.log.append(("install", name))
        return True, f"installed {name}"

    def uninstall(self, name: str) -> tuple[bool, str]:
        self.installed.discard(name)
        self.log.append(("uninstall", name))
        return True, f"uninstalled {name}"

    def update(self, name: str, spec: ToolInstallSpec, on_progress=None) -> tuple[bool, str]:
        self.log.append(("update", name))
        return True, f"updated {name}"


class _ExtTool(Tool):
    metadata = ToolMetadata(
        name="ext",
        description="ext tool",
        category="x",
        author="a",
        version="1",
        install=ToolInstallSpec(git_url="https://example.com/x.git"),
    )

    def get_metadata(self) -> ToolMetadata:
        return self.metadata

    def get_options(self) -> dict:
        return {}

    def set_option(self, key: str, value: str) -> None: ...

    def execute(self, context: object) -> object:
        return None


class _BuiltinTool(Tool):
    metadata = ToolMetadata(
        name="builtin", description="builtin tool", category="x", author="a", version="1"
    )

    def get_metadata(self) -> ToolMetadata:
        return self.metadata

    def get_options(self) -> dict:
        return {}

    def set_option(self, key: str, value: str) -> None: ...

    def execute(self, context: object) -> object:
        return None


def _ctx(manager, registry) -> CommandContext:
    return CommandContext(
        session={
            "tool_manager": manager,
            "tool_registry": registry,
            "renderer": None,
        },
        current_tool=None,
    )


def test_install_external():
    mgr = _FakeManager()
    reg = ToolRegistry()
    reg.register_tool(_ExtTool)
    out = InstallCommand().execute(_ctx(mgr, reg), ["ext"])
    assert out == "installed ext"
    assert ("install", "ext") in mgr.log


def test_install_builtin_rejected():
    mgr = _FakeManager()
    reg = ToolRegistry()
    reg.register_tool(_BuiltinTool)
    out = InstallCommand().execute(_ctx(mgr, reg), ["builtin"])
    assert "not an external tool" in out


def test_remove_external():
    mgr = _FakeManager()
    mgr.installed.add("ext")
    reg = ToolRegistry()
    reg.register_tool(_ExtTool)
    out = RemoveCommand().execute(_ctx(mgr, reg), ["ext"])
    assert out == "uninstalled ext"
    assert "ext" not in mgr.installed


def test_upgrade_external():
    mgr = _FakeManager()
    mgr.installed.add("ext")
    reg = ToolRegistry()
    reg.register_tool(_ExtTool)
    out = UpgradeCommand().execute(_ctx(mgr, reg), ["ext"])
    assert out == "updated ext"
    assert ("update", "ext") in mgr.log


def test_use_external_not_installed_hints_without_tty():
    mgr = _FakeManager()
    reg = ToolRegistry()
    reg.register_tool(_ExtTool)
    ctx = _ctx(mgr, reg)
    ctx.session["use_matches"] = ["ext"]
    out = UseCommand().execute(ctx, ["0"])
    assert out is None
    assert ctx.current_tool is None
