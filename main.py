"""Start Samuel Malíšek Klimabot web app on http://127.0.0.1:5000.

Usage (after `bash setup_project.sh` and activating .venv):
    python main.py
"""
import runpy
import time
from pathlib import Path


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


if __name__ == "__main__":
    log("Starting Samuel Malíšek Klimabot...")
    # Importing PyTorch is the slow, otherwise silent part of startup (minutes on /mnt/c in WSL).
    log("Loading libraries (PyTorch, sentence-transformers, Flask)...")
    start = time.time()
    import sentence_transformers  # noqa: F401
    import flask  # noqa: F401
    log(f"Libraries loaded in {time.time() - start:.0f}s. Loading knowledge base...")
    runpy.run_path(str(Path(__file__).resolve().parent / "web" / "web.py"), run_name="__main__")
