import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MODES = ["wall_unit", "holiday", "low", "normal", "high", "custom"]
BYPASS_MODES = ["auto", "closed", "open"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            VMCUbifluxSelect(api, entry.entry_id),
            VMCUbifluxBypassSelect(api, entry.entry_id),
        ],
        update_before_add=True,
    )


class VMCUbifluxSelect(SelectEntity):

    _attr_name = "Airflow Mode"
    _attr_options = MODES

    def __init__(self, api, entry_id):
        self.api = api
        self._entry_id = entry_id
        self._attr_unique_id = f"vmc_airflow_mode_{entry_id}"
        self._attr_current_option = None
        self._pending_option = None  # For optimistic update

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
    def current_option(self):
        if self._pending_option is not None:
            return self._pending_option
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Select new mode."""
        if option == "custom":
            # "custom" is a device state, not a settable mode: the unit enters it
            # when you set an Airflow Rate (the number entity), which is what makes
            # airflow_mode read back as "custom". Selecting it here would be a no-op
            # on the device, so ignore it and keep showing the real current mode.
            _LOGGER.debug(
                "Airflow Mode 'custom' is not directly selectable; set the Airflow Rate instead"
            )
            self.async_write_ha_state()
            return
        self._pending_option = option
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self.api.set_airflow_mode, option)
        # Do not set self._attr_current_option here, wait for update

    async def async_update(self) -> None:
        """Asynchronously update state."""
        data = await self.hass.async_add_executor_job(self.api.get_data)
        if data and "error" not in data:
            current_mode = data.get("airflow_mode")
            if current_mode in MODES:
                self._attr_current_option = current_mode
                if self._pending_option is not None and current_mode == self._pending_option:
                    self._pending_option = None


class VMCUbifluxBypassSelect(SelectEntity):

    _attr_name = "Bypass Mode"
    _attr_options = BYPASS_MODES

    def __init__(self, api, entry_id):
        self.api = api
        self._entry_id = entry_id
        self._attr_unique_id = f"vmc_bypass_mode_{entry_id}"
        self._attr_current_option = None
        self._pending_option = None  # For optimistic update

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
    def current_option(self):
        if self._pending_option is not None:
            return self._pending_option
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Select new bypass mode."""
        self._pending_option = option
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self.api.set_bypass_mode, option)
        # Do not set self._attr_current_option here, wait for update

    async def async_update(self) -> None:
        """Asynchronously update state."""
        data = await self.hass.async_add_executor_job(self.api.get_data)
        if data and "error" not in data:
            current_mode = data.get("bypass_mode")
            if current_mode in BYPASS_MODES:
                self._attr_current_option = current_mode
                if self._pending_option is not None and current_mode == self._pending_option:
                    self._pending_option = None
