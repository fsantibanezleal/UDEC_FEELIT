"""Static application configuration values."""

from app.core import version as _version

APP_NAME = _version.APP_NAME
APP_VERSION = _version.APP_VERSION
APP_PORT = 8101
APP_HOST = "127.0.0.1"
APP_DESCRIPTION = (
    "FeelIT is a modern accessibility-centered haptic platform for tactile 3D object "
    "exploration, Braille reading, and future haptic desktop interaction."
)
