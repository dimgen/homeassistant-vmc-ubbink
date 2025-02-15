from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

MODES = ["wall_unit", "holiday", "low", "normal", "high"]

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VMCUbifluxSelect(api, entry.entry_id)], True)

class VMCUbifluxSelect(SelectEntity):
    def __init__(self, api, entry_id):
        self.api = api
        self._attr_options = MODES
        self._attr_current_option = None
        self._entry_id = entry_id

    @property
    def name(self):
        return "VMC Airflow Mode"

    @property
    def unique_id(self):
        return f"vmc_airflow_mode"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "VMC Ubiflux",
            "manufacturer": "Ubbink",
            "model": "Vigor W325/W400",
            "entry_type": DeviceEntryType.SERVICE
        }

    def select_option(self, option: str):
        self.api.set_airflow_mode(option)
        self._attr_current_option = option