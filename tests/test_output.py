from sharkit.output.renderer import Renderer
from sharkit.output.theme import PINK, RESET, WHITE


def test_renderer_info(capsys):
    renderer = Renderer()
    renderer.info("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.out


def test_renderer_success(capsys):
    renderer = Renderer()
    renderer.success("Success message")
    captured = capsys.readouterr()
    assert "Success message" in captured.out


def test_renderer_warning(capsys):
    renderer = Renderer()
    renderer.warning("Warning message")
    captured = capsys.readouterr()
    assert "Warning message" in captured.out


def test_renderer_error(capsys):
    renderer = Renderer()
    renderer.error("Error message")
    captured = capsys.readouterr()
    assert "Error message" in captured.out


def test_renderer_panel(capsys):
    renderer = Renderer()
    renderer.panel("Title", "Content here")
    captured = capsys.readouterr()
    assert "Title" in captured.out
    assert "Content here" in captured.out
    assert "╭" in captured.out
    assert "╮" in captured.out
    assert "╰" in captured.out
    assert "╯" in captured.out


def test_renderer_raw(capsys):
    renderer = Renderer()
    renderer.raw("Raw text")
    captured = capsys.readouterr()
    assert "Raw text" in captured.out


def test_renderer_table(capsys):
    renderer = Renderer()
    renderer.table("Test", ["Name", "Value"], [["foo", "bar"], ["baz", "qux"]])
    captured = capsys.readouterr()
    assert "Name" in captured.out
    assert "Value" in captured.out
    assert "foo" in captured.out
    assert "bar" in captured.out
    assert "├" in captured.out
    assert "┤" in captured.out


def test_theme_colors_exist():
    assert PINK is not None
    assert WHITE is not None
    assert RESET is not None
