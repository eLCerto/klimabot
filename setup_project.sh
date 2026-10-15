#!/usr/bin/env bash
# Create .venv in this project and install the dependencies from pyproject.toml.
# Works on Linux/WSL/macOS and on Windows via Git Bash.
#
# Usage:  bash setup_project.sh            (create or update .venv)
#         bash setup_project.sh --recreate (delete .venv and start fresh)
# Then:   source .venv/bin/activate        (Git Bash on Windows: source .venv/Scripts/activate)
#         python main.py                   (web app on http://127.0.0.1:5000)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
cd "$PROJECT_DIR"

# venv layout differs between Windows (Scripts/) and POSIX (bin/).
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) VENV_BIN="$VENV_DIR/Scripts"; VENV_PY="$VENV_BIN/python.exe" ;;
    *)                    VENV_BIN="$VENV_DIR/bin";     VENV_PY="$VENV_BIN/python" ;;
esac

# Pick a working Python 3 interpreter (python3 on Windows may be the Store stub).
PYTHON=""
for cmd in python3 python "py -3"; do
    if $cmd -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
        PYTHON="$cmd"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.10+ not found. Install it and re-run." >&2
    exit 1
fi
echo "Using $($PYTHON --version) ($PYTHON)"

# Start fresh on request, or when .venv was made on another OS (e.g. Windows venv seen from WSL).
if [ -d "$VENV_DIR" ] && { [ "${1:-}" = "--recreate" ] || [ ! -x "$VENV_PY" ]; }; then
    echo "Removing existing .venv"
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in .venv"
    if ! $PYTHON -m venv "$VENV_DIR"; then
        rm -rf "$VENV_DIR"
        echo "Error: could not create venv. On Ubuntu run: sudo apt install python3-venv" >&2
        exit 1
    fi
fi

echo "Installing dependencies (sentence-transformers pulls in PyTorch, this can take a while)"
"$VENV_PY" -m pip install --upgrade pip
# On Linux, pip's default PyTorch is the CUDA build (several GB of nvidia-* packages).
# The bot only runs small embedding/reranker models, so install the CPU-only build first.
if [ "$(uname -s)" = "Linux" ]; then
    "$VENV_PY" -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu  # same pin as the Dockerfile
fi
# Install the dependencies declared in pyproject.toml.
"$VENV_PY" -m pip install .

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example - set ANTHROPIC_API_KEY in it."
fi

echo
echo "Done. Start the web app with:"
echo "  source ${VENV_BIN#"$PROJECT_DIR/"}/activate"
echo "  python main.py"
