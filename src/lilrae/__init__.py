"""Public package metadata for LilRAE."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lilrae")
except PackageNotFoundError:
    from lilrae._version import __version__

__all__ = ["__version__"]
