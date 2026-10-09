import asyncio
from types import SimpleNamespace

import pytest

from vmc_ubbink.number import VMCUbifluxNumber, async_setup_entry


class FakeAPI:
    def __init__(self, set_result=None):
        self.set_result = set_result or {"status": "ok"}

    def get_data(self):
        return {}

    def set_airflow_rate(self, rate):
        return self.set_result


class FakeHass:
    async def async_add_executor_job(self, target, *args):
        return target(*args)


def _number(model="W400", set_result=None):
    number = VMCUbifluxNumber(FakeAPI(set_result), "test-entry", model)
    number.hass = FakeHass()
    number.async_write_ha_state = lambda: None
    return number


def _setup_entry(data, options):
    added = []
    hass = SimpleNamespace(data={"vmc_ubbink": {"entry-1": FakeAPI()}})
    entry = SimpleNamespace(entry_id="entry-1", data=data, options=options)
    asyncio.run(
        async_setup_entry(hass, entry, lambda entities, **kwargs: added.extend(entities))
    )
    return added[0]


@pytest.mark.parametrize(
    ("model", "min_value", "max_value"),
    [("W325", 50, 325), ("W400", 50, 400), ("W600", 100, 600)],
)
def test_airflow_rate_bounds_follow_the_model(model, min_value, max_value):
    number = _number(model)

    assert number._attr_native_min_value == min_value
    assert number._attr_native_max_value == max_value


def test_legacy_entry_without_model_keeps_the_w400_range():
    # Entries created before the Model option existed must not change behaviour.
    number = _setup_entry({"host": "server.local", "port": 8085}, {})

    assert (number._attr_native_min_value, number._attr_native_max_value) == (50, 400)


def test_model_from_options_overrides_entry_data():
    number = _setup_entry({"model": "W400"}, {"model": "W600"})

    assert (number._attr_native_min_value, number._attr_native_max_value) == (100, 600)


def test_number_device_info_names_the_configured_model():
    number = _number("W600")

    assert number.device_info["model"] == "Vigor W600"
    assert number.device_info["identifiers"] == {("vmc_ubbink", "test-entry")}


def test_accepted_rate_stays_pending_until_the_unit_reads_it_back():
    number = _number("W600")
    number._attr_native_value = 150

    asyncio.run(number.async_set_native_value(500))

    assert number.native_value == 500


def test_rejected_rate_drops_the_optimistic_value():
    # e.g. a server not yet rebuilt for the W600 answers {"error": "Invalid rate..."}
    number = _number("W600", set_result={"error": "Invalid rate. Must be between 50 and 400 m³/h"})
    number._attr_native_value = 150

    asyncio.run(number.async_set_native_value(500))

    assert number.native_value == 150
