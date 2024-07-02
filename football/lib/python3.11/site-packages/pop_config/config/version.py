"""
Support embedding version number lookup into cli
"""
import importlib
import sys


def run(hub, primary):
    """
    Check the version number and then exit
    """
    v = hub.config.version.get(primary)

    print(f"{primary} {v}")
    sys.exit(0)


def get(hub, primary):
    try:
        mod = importlib.import_module(f"{primary}.version")
        return mod.version
    except ModuleNotFoundError as e:
        hub.log.warning(f"Could not find version.py for '{primary}': {e}")
