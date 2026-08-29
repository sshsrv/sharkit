from sharkit.config.manager import ConfigManager
from sharkit.config.paths import (
    get_cache_dir,
    get_config_dir,
    get_config_file,
    get_data_dir,
    get_history_file,
)


def test_config_dir_resolves_to_home():
    config_dir = get_config_dir()
    assert config_dir.name == "sharkit"
    assert ".config" in str(config_dir) or "config" in str(config_dir)


def test_config_file_is_in_config_dir():
    config_file = get_config_file()
    config_dir = get_config_dir()
    assert config_file.parent == config_dir


def test_history_file_is_in_config_dir():
    history_file = get_history_file()
    config_dir = get_config_dir()
    assert history_file.parent == config_dir


def test_cache_dir_is_in_config_dir():
    cache_dir = get_cache_dir()
    config_dir = get_config_dir()
    assert cache_dir.parent == config_dir


def test_data_dir_is_in_config_dir():
    data_dir = get_data_dir()
    config_dir = get_config_dir()
    assert data_dir.parent == config_dir


def test_config_manager_set_get(tmp_path, monkeypatch):
    monkeypatch.setattr("sharkit.config.manager.get_config_file", lambda: tmp_path / "config")
    monkeypatch.setattr("sharkit.config.manager.get_config_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_cache_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_history_file", lambda: tmp_path / "history")
    manager = ConfigManager()
    manager.set("test_key", "test_value")
    assert manager.get("test_key") == "test_value"


def test_config_manager_get_default(tmp_path, monkeypatch):
    monkeypatch.setattr("sharkit.config.manager.get_config_file", lambda: tmp_path / "config")
    monkeypatch.setattr("sharkit.config.manager.get_config_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_cache_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_history_file", lambda: tmp_path / "history")
    manager = ConfigManager()
    assert manager.get("nonexistent", "default") == "default"


def test_config_manager_has(tmp_path, monkeypatch):
    monkeypatch.setattr("sharkit.config.manager.get_config_file", lambda: tmp_path / "config")
    monkeypatch.setattr("sharkit.config.manager.get_config_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_cache_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_history_file", lambda: tmp_path / "history")
    manager = ConfigManager()
    assert not manager.has("missing")
    manager.set("existing", "value")
    assert manager.has("existing")


def test_config_manager_forward_compatible(tmp_path, monkeypatch):
    config_file = tmp_path / "config"
    config_file.write_text("unknown_key=unknown_value\ncurrent_key=current_value\n")
    monkeypatch.setattr("sharkit.config.manager.get_config_file", lambda: config_file)
    monkeypatch.setattr("sharkit.config.manager.get_config_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_cache_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sharkit.config.manager.get_history_file", lambda: tmp_path / "history")
    manager = ConfigManager()
    assert manager.get("current_key") == "current_value"
    assert manager.get("unknown_key") == "unknown_value"
