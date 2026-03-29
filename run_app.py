"""Standalone entry point for running FeelIT locally or from a frozen build."""

from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

import uvicorn

from app.core.config import APP_HOST, APP_NAME, APP_PORT
from app.main import app as feelit_app


def executable_directory() -> Path:
    """Return the directory containing the executable or script."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def main() -> None:
    """Launch the FeelIT ASGI application."""
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--host", default=APP_HOST)
    parser.add_argument("--port", type=int, default=APP_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    os.chdir(executable_directory())
    url = f"http://{args.host}:{args.port}"

    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    uvicorn.run(feelit_app, host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
