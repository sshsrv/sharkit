__app_name__ = "sharkit"

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("sharkit")
except Exception:
    __version__ = "0.2.0.dev1"
