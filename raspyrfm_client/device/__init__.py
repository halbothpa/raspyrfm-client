"""Compatibility wrappers for legacy ``raspyrfm_client.device`` imports.

Historically the project exposed device implementations under the
``raspyrfm_client.device`` namespace.  The code was later reorganised into
``raspyrfm_client.device_implementations`` but the documentation -- and any
third party integrations that relied on the old paths -- still import the
legacy modules.  Sphinx would therefore fail with ``ModuleNotFoundError``
when building the API reference.

This module repopulates the original namespace by re-exporting the new
implementation packages.  The helper walks through the manufacturer
subpackages and registers aliases inside :data:`sys.modules` so that direct
imports such as ``raspyrfm_client.device.manufacturer.elro.AB440D_200W``
continue to resolve correctly.
"""

from importlib import import_module
import pkgutil
import sys
from types import ModuleType
from typing import Dict

_BASE_MODULE = "raspyrfm_client.device_implementations.controlunit"
_MANUFACTURER_BASE = f"{_BASE_MODULE}.manufacturer"
_MANUFACTURER_CONSTANTS = "raspyrfm_client.device_implementations.manufacturer_constants"


def _alias_modules(mapping: Dict[str, str]) -> None:
    """Register aliases for modules that moved to new locations."""

    for alias, target in mapping.items():
        module = import_module(target)
        sys.modules[alias] = module
        globals()[alias.rsplit(".", 1)[-1]] = module


# Core control unit helpers -------------------------------------------------
_alias_modules(
    {
        __name__ + ".actions": f"{_BASE_MODULE}.actions",
        __name__ + ".base": f"{_BASE_MODULE}.base",
        __name__ + ".manufacturer_constants": _MANUFACTURER_CONSTANTS,
    }
)


def _mirror_package(alias: str, target: str) -> ModuleType:
    """Expose *target* package under *alias* in :data:`sys.modules`."""

    module = import_module(target)
    sys.modules[alias] = module
    globals()[alias.rsplit(".", 1)[-1]] = module
    return module


# Manufacturer subpackages --------------------------------------------------
manufacturer = _mirror_package(__name__ + ".manufacturer", _MANUFACTURER_BASE)

_MANUFACTURER_ALIAS = __name__ + ".manufacturer"
_MANUFACTURER_CONSTANTS_ALIAS = _MANUFACTURER_ALIAS + ".manufacturer_constants"

_alias_modules({_MANUFACTURER_CONSTANTS_ALIAS: _MANUFACTURER_CONSTANTS})

# ``manufacturer_constants`` used to live under ``raspyrfm_client.device.manufacturer``.
# Mirror that attribute onto the exported ``manufacturer`` package so attribute
# imports (``from raspyrfm_client.device.manufacturer import manufacturer_constants``)
# continue to work alongside module level aliases.
setattr(manufacturer, "manufacturer_constants", sys.modules[_MANUFACTURER_CONSTANTS_ALIAS])

for finder, name, ispkg in pkgutil.walk_packages(manufacturer.__path__, manufacturer.__name__ + "."):
    alias = name.replace(manufacturer.__name__, __name__ + ".manufacturer", 1)
    module = import_module(name)
    sys.modules[alias] = module


__all__ = [
    "actions",
    "base",
    "manufacturer",
    "manufacturer_constants",
]
