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
    """VigorDevice-like stub driven by direct._READERS (the source of truth).

    Each reader's getter returns the matching entry from `values`; readers not
    listed in `values` fall back to a deterministic placeholder, so adding a new
    entry to _READERS doesn't require touching this helper.
    """
    dev = MagicMock()
    for key, getter in direct._READERS.items():
        getattr(dev, getter).return_value = values.get(key, f"<{key}>")
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
    # Source of truth is the reader map, not a frozen snapshot: adding a sensor
    # to direct._READERS should not require editing this test.
    assert set(data.keys()) == set(direct._READERS)
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


def test_set_bypass_mode_delegates():
    dev = _device_returning(_FULL)
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    result = client.set_bypass_mode("open")
    dev.set_bypass_mode.assert_called_once_with("open")
    assert "error" not in result


def test_set_bypass_mode_invalidates_cache():
    dev = _device_returning(_FULL)
    clock = FakeClock()
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=clock)
    client.get_data()
    assert dev.get_serial_number.call_count == 1
    client.set_bypass_mode("closed")
    client.get_data()  # cache invalidated → re-poll even within TTL
    assert dev.get_serial_number.call_count == 2


def test_probe_success_returns_none():
    dev = _device_returning(_FULL)
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    assert client.probe() is None


def test_probe_cannot_reach_gateway_when_socket_refused():
    dev = _device_returning(_FULL)
    fake_client = MagicMock()
    fake_client.connect.return_value = False  # connection refused / timed out
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=fake_client, _clock=FakeClock()
    )
    assert client.probe() == "cannot_reach_gateway"
    dev.get_serial_number.assert_not_called()  # never reached the VMC


def test_probe_no_modbus_reply_when_read_raises():
    dev = _device_returning(_FULL)
    dev.get_serial_number.side_effect = vigor.ModbusError("no reply")
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    assert client.probe() == "no_modbus_reply"


def test_probe_no_modbus_reply_when_serial_empty():
    dev = _device_returning(_FULL)
    dev.get_serial_number.return_value = ""
    client = direct.DirectClient("1.2.3.4", 502, 20, _device=dev, _clock=FakeClock())
    assert client.probe() == "no_modbus_reply"
