"""Regression tests for the local FeelIT launcher."""

from __future__ import annotations

from unittest.mock import Mock

import run_app
from app.main import app as feelit_app


def test_run_app_main_passes_the_local_asgi_app_to_uvicorn(monkeypatch) -> None:
    uvicorn_run = Mock()
    monkeypatch.setattr(run_app.uvicorn, "run", uvicorn_run)
    monkeypatch.setattr(run_app.webbrowser, "open", Mock())
    monkeypatch.setattr(run_app.threading, "Timer", Mock())
    monkeypatch.setattr(run_app.sys, "argv", ["run_app.py", "--no-browser"])

    run_app.main()

    uvicorn_run.assert_called_once_with(
        feelit_app,
        host=run_app.APP_HOST,
        port=run_app.APP_PORT,
        reload=False,
    )
