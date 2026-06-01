from unittest.mock import MagicMock

import vigor


def _resp(registers, error=False):
    r = MagicMock()
    r.isError.return_value = error
    r.registers = registers
    return r


def test_convert_from_bcd():
    assert vigor.convert_from_bcd(0x1234) == 1234
    assert vigor.convert_from_bcd(0x0009) == 9


def test_serial_number_bcd_zfill():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([0x0012, 0x0034, 0x0056])
    dev = vigor.VigorDevice(client, slave=20)
    assert dev.get_serial_number() == "001200340056"
    client.read_input_registers.assert_called_once_with(4010, count=3, slave=20)


def test_supply_temperature_divides_by_ten():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([215])
    dev = vigor.VigorDevice(client, slave=20)
    assert dev.get_supply_temperature() == 21.5
    client.read_input_registers.assert_called_once_with(4036, count=1, slave=20)


def test_extract_temperature_divides_by_ten():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([189])
    dev = vigor.VigorDevice(client, slave=7)
    assert dev.get_extract_temperature() == 18.9
    client.read_input_registers.assert_called_once_with(4046, count=1, slave=7)


def test_humidity_passthrough():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([47])
    dev = vigor.VigorDevice(client, slave=20)
    assert dev.get_supply_humidity() == 47
    client.read_input_registers.assert_called_once_with(4037, count=1, slave=20)


def test_extract_humidity_register():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([55])
    dev = vigor.VigorDevice(client, slave=20)
    assert dev.get_extract_humidity() == 55
    client.read_input_registers.assert_called_once_with(4047, count=1, slave=20)


def test_pressure_and_airflow_registers():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([120])
    dev = vigor.VigorDevice(client, slave=20)
    assert dev.get_supply_pressure() == 120
    assert dev.get_extract_pressure() == 120
    assert dev.get_supply_airflow_preset() == 120
    assert dev.get_supply_airflow_actual() == 120
    assert dev.get_extract_airflow_preset() == 120
    assert dev.get_extract_airflow_actual() == 120
    addresses = [c.args[0] for c in client.read_input_registers.call_args_list]
    assert addresses == [4023, 4024, 4031, 4032, 4041, 4042]


def test_bypass_status_map():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_input_registers.return_value = _resp([3])
    assert dev.get_bypass_status() == "open"
    client.read_input_registers.return_value = _resp([4])
    assert dev.get_bypass_status() == "closed"
    client.read_input_registers.return_value = _resp([99])
    assert dev.get_bypass_status() == "unknown (99)"


def test_filter_status():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_input_registers.return_value = _resp([1])
    assert dev.get_filter_status() == "dirty"
    client.read_input_registers.return_value = _resp([0])
    assert dev.get_filter_status() == "normal"


def test_airflow_mode_wall_unit_and_custom_from_8000():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_holding_registers.return_value = _resp([0])
    assert dev.get_airflow_mode() == "wall_unit"
    client.read_holding_registers.return_value = _resp([2])
    assert dev.get_airflow_mode() == "custom"


def test_airflow_mode_reads_8001_when_modbus_control():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_holding_registers.side_effect = [_resp([1]), _resp([2])]
    assert dev.get_airflow_mode() == "normal"
    calls = [c.args[0] for c in client.read_holding_registers.call_args_list]
    assert calls == [8000, 8001]


def test_set_airflow_mode_sets_modbus_mode_then_writes_8001():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    # 8000 already = 1 (no rewrite needed), 8001 = 0 (must write high=3)
    client.read_holding_registers.side_effect = [_resp([1]), _resp([0])]
    client.write_register.return_value = _resp([], error=False)
    dev.set_airflow_mode("high")
    client.write_register.assert_called_once_with(8001, 3, slave=20)


def test_set_airflow_mode_wall_unit_writes_8000_zero():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_holding_registers.return_value = _resp([1])  # 8000 != 0 → write 0
    client.write_register.return_value = _resp([], error=False)
    dev.set_airflow_mode("wall_unit")
    client.write_register.assert_called_once_with(8000, 0, slave=20)


def test_set_custom_airflow_rate_clamps_and_sets_mode_2():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_holding_registers.return_value = _resp([2])  # 8000 already 2
    client.write_register.return_value = _resp([], error=False)
    dev.set_custom_airflow_rate(500)
    client.write_register.assert_called_once_with(8002, 400, slave=20)


def test_set_custom_airflow_rate_below_min_writes_zero():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    client.read_holding_registers.return_value = _resp([2])
    client.write_register.return_value = _resp([], error=False)
    dev.set_custom_airflow_rate(10)
    client.write_register.assert_called_once_with(8002, 0, slave=20)


def test_read_error_raises_modbus_error():
    client = MagicMock()
    client.read_input_registers.return_value = _resp([], error=True)
    dev = vigor.VigorDevice(client, slave=20)
    import pytest
    with pytest.raises(vigor.ModbusError):
        dev.get_supply_temperature()


def test_set_airflow_mode_ignores_unsupported_mode():
    client = MagicMock()
    dev = vigor.VigorDevice(client, slave=20)
    dev.set_airflow_mode("custom")
    client.write_register.assert_not_called()
    client.read_holding_registers.assert_not_called()
