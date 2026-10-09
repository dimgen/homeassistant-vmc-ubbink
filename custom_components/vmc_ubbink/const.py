from homeassistant.helpers.device_registry import DeviceEntryType

DOMAIN = "vmc_ubbink"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8085
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "secret"

# VMC connection mode
CONF_MODE = "mode"
MODE_SERVER = "server"
MODE_DIRECT = "direct"

# Direct (Waveshare TCP) parameters
CONF_SLAVE = "slave_id"
DEFAULT_TCP_PORT = 502   # Waveshare TCP port; separate from DEFAULT_PORT = 8085 (HTTP server)
DEFAULT_SLAVE = 20       # VMC Modbus slave address (UNIT in app/pyubbink.py)

# VMC model: selects the Airflow Rate range (m³/h) offered in Home Assistant.
# The ranges are the adjustable flow settings from the Ubbink installation
# manuals (menu 1.1-1.4); the unit itself rejects values outside its own range.
CONF_MODEL = "model"
MODELS = {
    "W225": (40, 225),
    "W325": (50, 325),
    "W400": (50, 400),
    "W600": (100, 600),
}
DEFAULT_MODEL = "W400"  # entries created before the option existed keep the 50-400 range


def get_entry_value(entry, key, default=None):
    return entry.options.get(key) if key in entry.options else entry.data.get(key, default)


def device_info(entry_id, model):
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "VMC Ubiflux",
        "manufacturer": "Ubbink",
        "model": f"Vigor {model}",
        "entry_type": DeviceEntryType.SERVICE,
    }
