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
    _attr_native_max_value = 400  # 220 for W325
    _attr_native_step = 1
    _attr_mode = "slider"

    def __init__(self, api, entry_id):
        self.api = api
        self._entry_id = entry_id
        self._attr_unique_id = f"vmc_airflow_rate_{entry_id}"
        self._attr_native_value = None  # Unknown yet
        self._pending_value = None  # For optimistic update

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "VMC Ubiflux",
            "manufacturer": "Ubbink",
            "model": "Vigor W325/W400",
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def native_value(self):
        if self._pending_value is not None:
            return self._pending_value
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        """Asynchronously set a new air flow value."""
        self._pending_value = int(value)
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self.api.set_airflow_rate, int(value))
        # Do not set self._attr_native_value here, wait for update

    async def async_update(self):
        """Asynchronously update state from external API."""
        data = await self.hass.async_add_executor_job(self.api.get_data)
        if data and "error" not in data:
            new_value = data.get("supply_airflow_preset", 50)
            self._attr_native_value = new_value
            if self._pending_value is not None and new_value == self._pending_value:
                self._pending_value = None
