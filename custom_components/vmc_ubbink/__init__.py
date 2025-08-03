from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME, DEFAULT_PASSWORD
from .api import VMCUbifluxAPI

PLATFORMS = ["sensor", "select", "number"]

def get_entry_value(entry, key, default=None):
    return entry.options.get(key) if key in entry.options else entry.data.get(key, default)

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    # Пересоздаём API с новыми параметрами
    api = VMCUbifluxAPI(
        get_entry_value(entry, "host", DEFAULT_HOST),
        get_entry_value(entry, "port", DEFAULT_PORT),
        get_entry_value(entry, "username", DEFAULT_USERNAME),
        get_entry_value(entry, "password", DEFAULT_PASSWORD),
    )
    hass.data[DOMAIN][entry.entry_id] = api

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    hass.data.setdefault(DOMAIN, {})

    try:
        api = VMCUbifluxAPI(
            get_entry_value(entry, "host", DEFAULT_HOST),
            get_entry_value(entry, "port", DEFAULT_PORT),
            get_entry_value(entry, "username", DEFAULT_USERNAME),
            get_entry_value(entry, "password", DEFAULT_PASSWORD),
        )
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = api

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok