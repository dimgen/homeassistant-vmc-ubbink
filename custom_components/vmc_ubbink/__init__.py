from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_MODE,
    MODE_SERVER,
    MODE_DIRECT,
    CONF_SLAVE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    DEFAULT_TCP_PORT,
    DEFAULT_SLAVE,
)
from .api import VMCUbifluxAPI

PLATFORMS = ["sensor", "select", "number"]


def get_entry_value(entry, key, default=None):
    return entry.options.get(key) if key in entry.options else entry.data.get(key, default)


def build_client(entry):
    """Build the client for the configured mode. Missing CONF_MODE => Server (backward compat)."""
    mode = get_entry_value(entry, CONF_MODE, MODE_SERVER)
    if mode == MODE_DIRECT:
        # Lazy import: pure Server users don't pull in pymodbus.
        from .direct import DirectClient

        return DirectClient(
            get_entry_value(entry, "host", DEFAULT_HOST),
            get_entry_value(entry, "port", DEFAULT_TCP_PORT),
            get_entry_value(entry, CONF_SLAVE, DEFAULT_SLAVE),
        )
    return VMCUbifluxAPI(
        get_entry_value(entry, "host", DEFAULT_HOST),
        get_entry_value(entry, "port", DEFAULT_PORT),
        get_entry_value(entry, "username", DEFAULT_USERNAME),
        get_entry_value(entry, "password", DEFAULT_PASSWORD),
    )


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    # Standard pattern: option edits actually take effect; entities are rebuilt with the
    # same unique_id (entry_id is unchanged) so history is preserved.
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    try:
        client = await hass.async_add_executor_job(build_client, entry)
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data[DOMAIN][entry.entry_id] = client

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        client = hass.data[DOMAIN].pop(entry.entry_id)
        close = getattr(client, "close", None)
        if callable(close):
            await hass.async_add_executor_job(close)
    return unload_ok
