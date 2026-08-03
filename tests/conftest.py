import enum
import sys
import types
from pathlib import Path

# Import the vmc_ubbink modules standalone (vigor.py / direct.py don't depend on HA),
# bypassing the package __init__.py (which pulls in homeassistant).
_PKG = Path(__file__).resolve().parent.parent / "custom_components" / "vmc_ubbink"
sys.path.insert(0, str(_PKG))

try:
    import homeassistant  # noqa: F401
except ImportError:
    # sensor.py imports homeassistant; stub the minimal surface it uses so the
    # tests keep running without a homeassistant install.
    _sensor = types.ModuleType("homeassistant.components.sensor")
    _sensor.SensorEntity = type("SensorEntity", (), {})
    _config_entries = types.ModuleType("homeassistant.config_entries")
    _config_entries.ConfigEntry = type("ConfigEntry", (), {})
    _core = types.ModuleType("homeassistant.core")
    _core.HomeAssistant = type("HomeAssistant", (), {})
    _device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    _device_registry.DeviceEntryType = enum.Enum("DeviceEntryType", {"SERVICE": "service"})
    sys.modules["homeassistant"] = types.ModuleType("homeassistant")
    sys.modules["homeassistant.components"] = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components.sensor"] = _sensor
    sys.modules["homeassistant.config_entries"] = _config_entries
    sys.modules["homeassistant.core"] = _core
    sys.modules["homeassistant.helpers"] = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers.device_registry"] = _device_registry

# Register the package itself without executing its __init__.py, so sensor.py
# is importable as vmc_ubbink.sensor and its `from .const import DOMAIN` resolves.
_pkg_mod = types.ModuleType("vmc_ubbink")
_pkg_mod.__path__ = [str(_PKG)]
sys.modules["vmc_ubbink"] = _pkg_mod
