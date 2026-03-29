# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for FeelIT."""

from pathlib import Path

APP_NAME = "FeelIT"
ENTRY_POINT = "run_app.py"
VERSION_FILE = "installer/pyinstaller_version_info.txt"

datas = []
static_dir = Path("app/static")
if static_dir.exists():
    datas.append((str(static_dir), "app/static"))

a = Analysis(
    [ENTRY_POINT],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn.lifespan.on",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.websockets_impl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "jupyter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    version=VERSION_FILE,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
