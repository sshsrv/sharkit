<div align="center"><img width="640" height="347" alt="banner" src="https://github.com/user-attachments/assets/c027fb38-fe0f-4baa-b35f-597f9f8cf39b" /></div>

<div align="center">
  
![PyPI](https://img.shields.io/pypi/v/sharkit?labelColor=000000&color=ff5faf&style=flat)
![Python](https://img.shields.io/pypi/pyversions/sharkit?labelColor=000000&color=ff5faf&style=flat)
![License](https://img.shields.io/pypi/l/sharkit?labelColor=000000&color=ff5faf&style=flat)
![CI](https://img.shields.io/github/actions/workflow/status/sshsrv/sharkit/ci.yml?labelColor=000000&color=ff5faf&style=flat)

</div>

> [!IMPORTANT]  
> sharkit is intended for lawful OSINT research, authorized security testing, education, and legitimate investigations. You are responsible for complying with applicable laws, permissions, and terms of service.
> 
> sharkit does not guarantee anonymity.
#

### Features
- A terminal framework for OSINT / HUMINT / GEOINT work.
- Modules expose a `run` method, options, and metadata; the shell loads them as you need them.
- 15 built-in commands: `use`, `run`, `set`, `search`, `history`, `clear`, `exit`, and a few more.
- Ships with two example modules: `testing/demo/echo` and `testing/http/metadata`.
- `sharkit --version` shows the exact build you have, dev pre-releases included.
- State lives in `~/.config/sharkit` and runs fine on Termux / Android.
- To wipe it completely: `uv tool uninstall sharkit` and `rm -rf ~/.config/sharkit`.
#

### sharkit management on Linux using uv (RECOMMENDED)
- Install
```bash
uv tool install sharkit
```
- Upgrade
```bash
uv tool upgrade sharkit
```
- Uninstall
```bash
uv tool uninstall sharkit
rm -rf ~/.config/sharkit
```
<br>

### sharkit management on Linux using pip
- Install
```bash
pip install sharkit
```
- Upgrade
```bash
pip install --upgrade sharkit
```
- Uninstall
```bash
pip uninstall sharkit
rm -rf ~/.config/sharkit
```
#

### Links
- PyPI: https://pypi.org/project/sharkit/
- GitHub: https://github.com/sshsrv/sharkit
- Releases: https://github.com/sshsrv/sharkit/releases