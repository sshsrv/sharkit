from sharkit.history.manager import HistoryManager


def _make_manager(tmp_path, monkeypatch):
    history_file = tmp_path / "history"
    monkeypatch.setattr("sharkit.history.manager.get_history_file", lambda: history_file)
    return HistoryManager()


def test_history_manager_add_and_get(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.add_command("help")
    manager.add_command("use blackbird")
    history = manager.get_history()
    assert "help" in history
    assert "use blackbird" in history


def test_history_manager_persistence(tmp_path, monkeypatch):
    history_file = tmp_path / "history"
    monkeypatch.setattr("sharkit.history.manager.get_history_file", lambda: history_file)
    manager1 = HistoryManager()
    manager1.add_command("test_command")
    manager2 = HistoryManager()
    history = manager2.get_history()
    assert "test_command" in history


def test_history_manager_filters_sensitive(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.add_command("set password mysecret")
    manager.add_command("set token abc123")
    manager.add_command("help")
    history = manager.get_history()
    assert "set password mysecret" not in history
    assert "set token abc123" not in history
    assert "help" in history


def test_history_manager_search(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.add_command("use blackbird")
    manager.add_command("use recon")
    manager.add_command("help")
    results = manager.search("use")
    assert len(results) == 2
    assert "help" not in results


def test_history_manager_clear(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.add_command("test")
    manager.clear()
    history = manager.get_history()
    assert len(history) == 0


def test_history_manager_limit(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    for i in range(10):
        manager.add_command(f"command_{i}")
    history = manager.get_history(limit=5)
    assert len(history) == 5


def test_history_manager_deduplicates_consecutive(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.add_command("help")
    manager.add_command("help")
    manager.add_command("help")
    history = manager.get_history()
    assert history.count("help") == 1
