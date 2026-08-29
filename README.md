# sharkit

OSINT / HUMINT / GEOINT research framework — a modular CLI for gathering and correlating
open-source intelligence from the terminal.

> Built for Linux. Runs anywhere Python 3.11+ runs — including **Termux on Android**.

## Requirements

- Python >= 3.11
- `pip` or `uv`

## Installation

From PyPI:

```bash
pip install sharkit
```

Or with `uv`:

```bash
uv tool install sharkit
```

Then launch the interactive shell:

```bash
sharkit
```

## Termux / Android

sharkit is pure Python (no compiled extensions) and depends only on `prompt_toolkit`
and `httpx`, so it installs and runs on Termux without any native build step.

```bash
pkg update && pkg install python
pip install sharkit
sharkit
```

If Termux's Python is marked *externally managed*, install into a virtual environment:

```bash
pkg install python
python -m venv ~/sharkit-venv
~/sharkit-venv/bin/pip install sharkit
~/sharkit-venv/bin/sharkit
```

- Configuration, history and cache live under `~/.config/sharkit`
  (on Android: `/data/data/com.termux/files/home/.config/sharkit`).
- Network access uses the standard Termux permission — no extra setup required.
- The UI relies on ANSI escape codes and Unicode box-drawing, which Termux's
  terminal renders natively.

## Quick start

```
sharkit                      # start the interactive shell
help                        # list commands
use testing/demo/echo       # load a module
set message "hello"         # configure an option
run                         # execute the active module
history                     # show command history
clear                       # clear the screen
exit                        # quit
```

Available commands: `help`, `banner`, `version`, `status`, `use`, `back`, `info`,
`show`, `set`, `unset`, `run`, `search`, `history`, `clear`, `exit`.

## Modules

Modules are discovered automatically from the packaged `sharkit/modules` directory:

- `testing/demo/echo` — echo module for testing the framework
- `testing/http/metadata` — HTTP metadata gathering (status, headers, content type, …)

## Development

```bash
git clone https://github.com/sshsrv/sharkit
cd sharkit
uv sync --all-groups
uv run sharkit
```

Quality gates: `uv run ruff check .`, `uv run mypy src/`, `uv run pytest -q`.

## Disclaimer

sharkit is a research tool. Use it responsibly and in accordance with applicable law
and the terms of service of any system you interact with.
