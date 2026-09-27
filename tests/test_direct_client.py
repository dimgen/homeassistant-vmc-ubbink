from unittest.mock import MagicMock, call

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


@pytest.mark.parametrize("error_type", [ConnectionResetError, BrokenPipeError])
def test_transport_failure_reconnects_and_caches_fresh_poll(error_type):
    dev = _device_returning(_FULL)
    # Fail partway through the poll: the retry must re-read earlier fields too.
    dev.get_serial_number.side_effect = ["old serial", "new serial"]
    dev.get_supply_temperature.side_effect = [error_type("connection lost"), 22.0]
    transport = MagicMock(connected=True)
    clock = FakeClock()
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=transport, _clock=clock
    )
    events = MagicMock()
    events.attach_mock(dev.get_serial_number, "read_serial")
    events.attach_mock(transport.close, "close")
    events.attach_mock(transport.connect, "connect")

    def reconnect():
        assert client._lock.locked()
        clock.t += direct.CACHE_TTL + 1
        return True

    transport.connect.side_effect = reconnect

    data = client.get_data()

    assert data["serial_number"] == "new serial"
    assert data["supply_temperature"] == 22.0
    assert events.mock_calls == [
        call.read_serial(), call.close(), call.connect(), call.read_serial()
    ]
    # Cache lifetime starts after recovery, not before the failed poll.
    assert client.get_data() is data
    assert dev.get_serial_number.call_count == 2


@pytest.mark.parametrize("failure", ["refused", "connect_error", "poll_error"])
def test_failed_recovery_returns_error_and_next_poll_can_recover(failure):
    dev = _device_returning(_FULL)
    clock = FakeClock()
    transport = MagicMock(connected=True)
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=transport, _clock=clock
    )
    client.get_data()  # Seed a cache which must not hide subsequent failures.
    clock.t += direct.CACHE_TTL + 1
    dev.get_serial_number.reset_mock()
    dev.get_serial_number.side_effect = ConnectionResetError("connection lost")
    expected = "connection lost"
    expected_reads = 1
    if failure == "refused":
        transport.connect.return_value = False
    elif failure == "connect_error":
        transport.connect.side_effect = OSError("gateway unavailable")
        expected = "gateway unavailable"
    else:
        transport.connect.return_value = True
        dev.get_serial_number.side_effect = [
            ConnectionResetError("connection lost"), BrokenPipeError("retry failed")
        ]
        expected = "retry failed"
        expected_reads = 2

    assert client.get_data() == {"error": expected}
    transport.close.assert_called_once()
    transport.connect.assert_called_once()
    assert dev.get_serial_number.call_count == expected_reads

    # No TTL wait or integration reload is needed once the gateway recovers.
    transport.connected = False
    transport.connect.side_effect = None
    transport.connect.return_value = True
    dev.get_serial_number.side_effect = None
    assert client.get_data()["serial_number"] == _FULL["serial_number"]
    assert transport.connect.call_count == 2


def test_initial_connection_exception_can_recover():
    dev = _device_returning(_FULL)
    transport = MagicMock(connected=False)
    transport.connect.side_effect = [OSError("connection lost"), True]
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=transport, _clock=FakeClock()
    )

    assert client.get_data()["serial_number"] == _FULL["serial_number"]
    transport.close.assert_called_once()
    assert transport.connect.call_count == 2
    dev.get_serial_number.assert_called_once()


@pytest.mark.parametrize("error_type", [vigor.ModbusError, IndexError])
def test_field_error_does_not_reconnect(error_type):
    dev = _device_returning(_FULL)
    dev.get_supply_humidity.side_effect = error_type("unsupported register")
    transport = MagicMock(connected=True)
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=transport, _clock=FakeClock()
    )

    data = client.get_data()
    assert data["supply_humidity"] is None
    assert data["supply_temperature"] == _FULL["supply_temperature"]
    transport.close.assert_not_called()
    transport.connect.assert_not_called()


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


def test_probe_cannot_reach_gateway_when_connect_raises_oserror():
    dev = _device_returning(_FULL)
    fake_client = MagicMock()
    fake_client.connect.side_effect = OSError("[Errno 111] Connection refused")
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=fake_client, _clock=FakeClock()
    )
    assert client.probe() == "cannot_reach_gateway"
    dev.get_serial_number.assert_not_called()


def test_probe_success_via_real_client_connect():
    dev = _device_returning(_FULL)
    fake_client = MagicMock()
    fake_client.connect.return_value = True  # exercise the production connect() branch
    client = direct.DirectClient(
        "1.2.3.4", 502, 20, _device=dev, _client=fake_client, _clock=FakeClock()
    )
    assert client.probe() is None
    fake_client.connect.assert_called_once()
    dev.get_serial_number.assert_called_once()
