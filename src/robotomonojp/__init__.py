"""RobotoMonoJP font generator."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("robotomonojp")
except PackageNotFoundError:
    __version__ = "0.0.0+local"
