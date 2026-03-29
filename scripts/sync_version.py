"""Synchronize derived version files from the canonical FeelIT version."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.version import APP_NAME, APP_PUBLISHER, APP_VERSION, WINDOWS_FILE_VERSION

INSTALLER_DIR = ROOT / "installer"
ISS_VERSION_FILE = INSTALLER_DIR / "version.iss"
PYINSTALLER_VERSION_FILE = INSTALLER_DIR / "pyinstaller_version_info.txt"


def build_iss_file() -> str:
    """Build the generated Inno Setup version include file."""
    return (
        f'#define AppName "{APP_NAME}"\n'
        f'#define AppVersion "{APP_VERSION}"\n'
        f'#define AppPublisher "{APP_PUBLISHER}"\n'
        f'#define AppExeName "{APP_NAME}.exe"\n'
    )


def build_pyinstaller_version_file() -> str:
    """Build the Windows version metadata for PyInstaller."""
    major, minor, patch, build = (int(part) for part in WINDOWS_FILE_VERSION.split("."))
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{APP_PUBLISHER}'),
          StringStruct('FileDescription', '{APP_NAME}'),
          StringStruct('FileVersion', '{WINDOWS_FILE_VERSION}'),
          StringStruct('InternalName', '{APP_NAME}'),
          StringStruct('OriginalFilename', '{APP_NAME}.exe'),
          StringStruct('ProductName', '{APP_NAME}'),
          StringStruct('ProductVersion', '{APP_VERSION}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)"""


def write_if_changed(path: Path, content: str) -> None:
    """Write a file only when its content changed."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def main() -> None:
    """Synchronize all derived version artifacts."""
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    write_if_changed(ISS_VERSION_FILE, build_iss_file())
    write_if_changed(PYINSTALLER_VERSION_FILE, build_pyinstaller_version_file())
    print(APP_VERSION)


if __name__ == "__main__":
    main()
