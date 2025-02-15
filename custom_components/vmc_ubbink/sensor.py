from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType
from .const import DOMAIN

SENSOR_TYPES = {
    "supply_temperature": ("Supply Temperature", "°C"),
    "supply_pressure": ("Supply Pressure", "Pa"),
    "supply_airflow_actual": ("Supply Airflow Actual", "m³/h"),
    "supply_airflow_preset": ("Supply Airflow Preset", "m³/h"),
    "extract_temperature": ("Extract Temperature", "°C"),
    "extract_pressure": ("Extract Pressure", "Pa"),
    "extract_airflow_actual": ("Extract Airflow Actual", "m³/h"),
    "extract_airflow_preset": ("Extract Airflow Preset", "m³/h"),
    "airflow_mode": ("Airflow Mode", ""),
    "bypass_status": ("Bypass Status", ""),
    "filter_status": ("Filter Status", ""),
    "serial_number": ("Serial Number", ""),
}

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]
    sensors = [VMCUbifluxSensor(api, entry.entry_id, sensor_type) for sensor_type in SENSOR_TYPES]
    async_add_entities(sensors, True)

class VMCUbifluxSensor(Entity):
    def __init__(self, api, entry_id, sensor_type):
        self.api = api
        self._sensor_type = sensor_type
        self._name, self._unit = SENSOR_TYPES[sensor_type]
        self._state = None
        self._entry_id = entry_id

    @property
    def name(self):
        return f"VMC {self._name}"

    @property
    def unique_id(self):
        return f"vmc_{self._sensor_type}"

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit if self._unit else None

    @property
    def extra_state_attributes(self):
        return {"type": self._sensor_type}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "VMC Ubiflux",
            "manufacturer": "Ubbink",
            "model": "Vigor W400",
            "entry_type": DeviceEntryType.SERVICE
        }

    def update(self):
        data = self.api.get_data()
        if "error" in data:
            self._state = "error"
        else:
            self._state = data.get(self._sensor_type, "unknown")