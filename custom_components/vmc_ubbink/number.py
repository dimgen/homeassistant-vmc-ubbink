from homeassistant.components.number import NumberEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VMCUbifluxNumber(api, entry.entry_id)], True)

class VMCUbifluxNumber(NumberEntity):
    def __init__(self, api, entry_id):
        self.api = api
        self._attr_name = "Airflow Rate"
        self._attr_min_value = 50
        self._attr_max_value = 400
        self._attr_step = 5
        self._attr_value = None
        self._entry_id = entry_id

    @property
    def name(self):
        return "VMC Airflow Rate"

    @property
    def unique_id(self):
        return f"vmc_airflow_rate"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "VMC Ubiflux",
            "manufacturer": "Ubbink",
            "model": "Vigor W325/W400",
            "entry_type": DeviceEntryType.SERVICE
        }

    def set_value(self, value: float):
        self.api.set_airflow_rate(int(value))
        self._attr_value = int(value)