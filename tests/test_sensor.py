import asyncio

import pytest

from vmc_ubbink.sensor import SENSOR_TYPES, VMCUbifluxSensor


ENUM_OPTIONS = {
    "airflow_mode": ["wall_unit", "custom", "holiday", "low", "normal", "high"],
    "bypass_status": ["initializing", "opening", "closing", "open", "closed"],
    "filter_status": ["normal", "dirty"],
}


class FakeAPI:
    def __init__(self, data):
        self.data = data

    def get_data(self):
        return self.data


class FakeHass:
    async def async_add_executor_job(self, target):
        return target()


def _sensor(sensor_type, value):
    sensor = VMCUbifluxSensor(
        FakeAPI({sensor_type: value}),
        "test-entry",
        sensor_type,
        SENSOR_TYPES[sensor_type],
    )
    sensor.hass = FakeHass()
    return sensor


@pytest.mark.parametrize(("sensor_type", "options"), ENUM_OPTIONS.items())
def test_enum_sensor_declares_options(sensor_type, options):
    sensor = _sensor(sensor_type, options[0])

    assert sensor._attr_device_class == "enum"
    assert sensor._attr_options == options


@pytest.mark.parametrize(("sensor_type", "options"), ENUM_OPTIONS.items())
def test_enum_sensor_accepts_supported_state(sensor_type, options):
    sensor = _sensor(sensor_type, options[-1])

    asyncio.run(sensor.async_update())

    assert sensor._attr_native_value == options[-1]


@pytest.mark.parametrize("sensor_type", ENUM_OPTIONS)
def test_enum_sensor_maps_unsupported_state_to_unknown(sensor_type):
    sensor = _sensor(sensor_type, "unknown (99)")

    asyncio.run(sensor.async_update())

    assert sensor._attr_native_value is None
