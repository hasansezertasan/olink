"""olink - Open external URLs related to your project."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("olink")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

from olink.cli import main

__all__ = ["main", "__version__"]
