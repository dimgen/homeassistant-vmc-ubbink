from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .api import VMCUbifluxAPI

PLATFORMS = ["sensor", "select", "number"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    hass.data.setdefault(DOMAIN, {})

    try:
        api = VMCUbifluxAPI(
            entry.data["host"],
            entry.data["port"],
            entry.data["username"],
            entry.data["password"],
        )
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok