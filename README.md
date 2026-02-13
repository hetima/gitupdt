# gitupdt

A Python tool for easily updating Git repositories. It checks for updates in remote repositories and allows you to pull branches or switch to tags through an interactive menu.

**This tool is intended for use in execution-only repositories that are cloned for software usage purposes, without making edits. It is not recommended for use in development repositories.**


## Features

- **Remote update check**: Check if there are updates in the remote repository
- **Interactive selection menu**: Interactive CLI powered by questionary
- **Branch pull**: Update the current branch to the latest state
- **Checkout to tag**: Switch to a specified version tag
- **Reset mode**: Use `git reset --hard` with the `--reset` option to update
- **requirements.txt change display and installation**: Display changes in dependency files and support automatic installation
- **pyproject.toml change display and uv sync**: Detect changes in pyproject.toml dependencies section and run uv sync when uv is installed
- **Automatic virtual environment detection**: Automatically detect `.venv` or `venv` folders and display appropriate Python interpreter options
- **Repository maintenance**: Automatically run `git gc --auto` after updates

## Installation

```bash
pip install gitupdt
```

## Usage

### Update repository in current directory

```bash
gitupdt
```

### Update repository at specified path

```bash
gitupdt /path/to/repo
```

### Update with reset mode

When you specify the `--reset` option, it uses `git reset --hard` instead of `git checkout` or `git pull` to update. This is useful for forcibly overwriting a local file with a remote one when the local file is corrupted.

```bash
gitupdt --reset
```

```bash
gitupdt /path/to/repo --reset
```

## Available Actions

When you run the tool, you can select from the following actions:

1. **Checkout and Pull latest remote**: Checkout and pull the remote default branch
2. **Pull**: Update the current branch to the latest state (when behind remote)
3. **Checkout to tag**: Switch to a specified version tag (select from latest or past tags)

### Automatic Installation on requirements.txt Changes

When there are changes in `requirements.txt`, the following process occurs:

1. Changes are displayed in unified diff format
2. You are prompted whether to install the updated `requirements.txt`
3. You can select the appropriate install command:
   - If uv is installed: `uv pip install` or `uv add` (only if pyproject.toml exists)
   - Currently running Python
   - Detected virtual environment (`.venv` or `venv`) Python
4. Installation is executed with the selected command
5. You can also choose to cancel and install manually later

The script traverses the repository folders upward. If it finds a folder named `.venv` or `venv`, it checks whether it's a venv environment and presents it as an option. This allows installation from outside a venv environment, but it's safer to activate venv beforehand.

### Automatic uv sync on pyproject.toml Changes

If uv is installed and `pyproject.toml` exists, the following process occurs:

1. Changes in the `dependencies` section of `pyproject.toml` are displayed in unified diff format
2. You are prompted whether to run `uv sync` to update dependencies
3. If you choose `uv sync`, dependencies will be updated
4. You can also choose to cancel and update manually later

Note: If there are changes in `pyproject.toml`, the `requirements.txt` change confirmation will not be performed.

## Changelog

### 1.0.1
- Added uv support for package installation
  - `uv pip install` and `uv add` options are now available when uv is installed
- Added pyproject.toml change detection and uv sync
  - Detects changes in the `dependencies` section of `pyproject.toml`
  - Automatically prompts to run `uv sync` when changes are detected
- Changed minimum Python version from 3.9 to 3.11 (due to tomllib usage)

## Dependencies

- GitPython
- questionary
- packaging

## Python Version

Python 3.11 or higher is required.

## License

MIT License
