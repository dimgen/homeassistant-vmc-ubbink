from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from datetime import timedelta

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)  # scan every 30 seconds

SENSOR_TYPES = {
    "supply_temperature": {
        "name": "Supply Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "supply_pressure": {
        "name": "Supply Pressure",
        "unit": "Pa",
        "device_class": "pressure",
        "state_class": "measurement",
    },
    "supply_airflow_actual": {
        "name": "Supply Airflow Actual",
        "unit": "m³/h",
        # here we can set our own custom device_class (HA does not have one ready for air consumption yet)
    },
    "supply_airflow_preset": {
        "name": "Supply Airflow Preset",
        "unit": "m³/h",
    },
    "extract_temperature": {
        "name": "Extract Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "extract_pressure": {
        "name": "Extract Pressure",
        "unit": "Pa",
        "device_class": "pressure",
        "state_class": "measurement",
    },
    "extract_airflow_actual": {
        "name": "Extract Airflow Actual",
        "unit": "m³/h",
    },
    "extract_airflow_preset": {
        "name": "Extract Airflow Preset",
        "unit": "m³/h",
    },
    "airflow_mode": {
        "name": "Airflow Mode",
        "unit": None,  # just a string
    },
    "bypass_status": {
        "name": "Bypass Status",
        "unit": None,
    },
    "filter_status": {
        "name": "Filter Status",
        "unit": None,
    },
    "serial_number": {
        "name": "Serial Number",
        "unit": None,
    },
}


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities
):
    api = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for sensor_type, params in SENSOR_TYPES.items():
        sensors.append(VMCUbifluxSensor(api, entry.entry_id, sensor_type, params))

    # update_before_add=True will force Home Assistant to call update/async_update for each entity
    async_add_entities(sensors, update_before_add=True)


class VMCUbifluxSensor(SensorEntity):

    def __init__(self, api, entry_id, sensor_type, params):
        self.api = api
        self._entry_id = entry_id
        self._sensor_type = sensor_type
        self._params = params

        self._attr_name = params["name"]
        self._attr_unique_id = f"vmc_{sensor_type}_{entry_id}"

        # If we know for sure that this is a numeric sensor, we can use:
        # self._attr_native_unit_of_measurement = ...
        # self._attr_device_class = ...
        # But to keep things simple, we'll leave the universal version:
        self._attr_native_unit_of_measurement = params["unit"]
        self._attr_device_class = params.get("device_class")
        self._attr_state_class = params.get("state_class")

        # State will be stored in _attr_native_value
        self._attr_native_value = None

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
    def extra_state_attributes(self):
        return {
            "type": self._sensor_type
        }

    async def async_update(self):
        data = await self.hass.async_add_executor_job(self.api.get_data)

        if not data or "error" in data:
            self._attr_native_value = None
        else:
            self._attr_native_value = data.get(self._sensor_type, None)