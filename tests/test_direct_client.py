from unittest.mock import MagicMock

import pytest

import direct
import vigor


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _device_returning(values):
    """VigorDevice-like stub: each get_* returns the value from `values` by key."""
    dev = MagicMock()
    dev.get_serial_number.return_value = values["serial_number"]
    dev.get_supply_temperature.return_value = values["supply_temperature"]
    dev.get_supply_pressure.return_value = values["supply_pressure"]
    dev.get_supply_humidity.return_value = values["supply_humidity"]
    dev.get_supply_airflow_actual.return_value = values["supply_airflow_actual"]
    dev.get_supply_airflow_preset.return_value = values["supply_airflow_preset"]
    dev.get_extract_temperature.return_value = values["extract_temperature"]
    dev.get_extract_pressure.return_value = values["extract_pressure"]
    dev.get_extract_humidity.return_value = values["extract_humidity"]
    dev.get_extract_airflow_actual.return_value = values["extract_airflow_actual"]
    dev.get_extract_airflow_preset.return_value = values["extract_airflow_preset"]
    dev.get_airflow_mode.return_value = values["airflow_mode"]
    dev.get_bypass_status.return_value = values["bypass_status"]
    dev.get_filter_status.return_value = values["filter_status"]
    return dev


_FULL = {
    "serial_number": "001200340056",
    "supply_temperature": 21.5,
    "supply_pressure": 30,
    "supply_humidity": 45,
    "supply_airflow_actual": 150,
    "supply_airflow_preset": 150,
    "extract_temperature": 20.0,
    "extract_pressure": 28,
    "extract_humidity": 50,
    "extract_airflow_actual": 150,
    "extract_airflow_preset": 150,
    "airflow_mode": "normal",
    "bypass_status": "open",
    "filter_status": "normal",
}


def test_get_data_returns_all_keys():
    dev = _device_returning(_FULL)
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    data = client.get_data()
    assert set(data.keys()) == set(_FULL.keys())
    assert data["supply_temperature"] == 21.5
    assert data["supply_humidity"] == 45


def test_get_data_caches_within_ttl():
    dev = _device_returning(_FULL)
    clock = FakeClock()
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=clock)
    client.get_data()
    client.get_data()  # within TTL → no second poll
    assert dev.get_serial_number.call_count == 1


def test_get_data_repolls_after_ttl():
    dev = _device_returning(_FULL)
    clock = FakeClock()
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=clock)
    client.get_data()
    clock.t += 10  # > CACHE_TTL
    client.get_data()
    assert dev.get_serial_number.call_count == 2


def test_field_level_error_becomes_none():
    dev = _device_returning(_FULL)
    dev.get_supply_humidity.side_effect = vigor.ModbusError("boom")
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    data = client.get_data()
    assert data["supply_humidity"] is None
    assert data["supply_temperature"] == 21.5  # other fields still populated


def test_set_airflow_rate_invalidates_cache():
    dev = _device_returning(_FULL)
    clock = FakeClock()
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=clock)
    client.get_data()
    assert dev.get_serial_number.call_count == 1
    client.set_airflow_rate(200)
    dev.set_custom_airflow_rate.assert_called_once_with(200)
    client.get_data()  # cache invalidated → re-poll even within TTL
    assert dev.get_serial_number.call_count == 2


def test_set_airflow_mode_delegates():
    dev = _device_returning(_FULL)
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    client.set_airflow_mode("high")
    dev.set_airflow_mode.assert_called_once_with("high")


def test_set_bypass_mode_is_noop():
    dev = _device_returning(_FULL)
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    result = client.set_bypass_mode("auto")
    assert "error" not in result
    assert not dev.method_calls or all(
        not str(c).startswith("set_bypass_mode") for c in dev.method_calls
    )
