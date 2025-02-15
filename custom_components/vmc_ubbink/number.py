from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VMCUbifluxNumber(api, entry.entry_id)], update_before_add=True)


class VMCUbifluxNumber(NumberEntity):
    _attr_name = "Airflow Rate"
    _attr_native_min_value = 50
    _attr_native_max_value = 400
    _attr_native_step = 5

    def __init__(self, api, entry_id):
        self.api = api
        self._entry_id = entry_id
        self._attr_unique_id = f"vmc_airflow_rate_{entry_id}"
        self._attr_native_value = None  # Unknown yet

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "VMC Ubiflux",
            "manufacturer": "Ubbink",
            "model": "Vigor W325/W400",
            "entry_type": DeviceEntryType.SERVICE,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Asynchronously set a new air flow value."""
        # If the API method is synchronous, then wrap it in executor_job:
        await self.hass.async_add_executor_job(self.api.set_airflow_rate, int(value))
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    async def async_update(self):
        """Asynchronously update state from external API."""
        # Similarly, if get_data() method is synchronous, call via executor_job
        data = await self.hass.async_add_executor_job(self.api.get_data)
        if data and "error" not in data:
            # Get the current value of the preset
            self._attr_native_value = data.get("supply_airflow_preset", 50)
