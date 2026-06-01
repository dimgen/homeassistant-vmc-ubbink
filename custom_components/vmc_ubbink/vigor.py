"""Thin pymodbus 3.x wrapper around the Ubbink Ubiflux Vigor registers.

Line-by-line port of ubbink-server/app/pyubbink.py. Differences from the original
(which targets pymodbus 2.5.3):
- kwarg `unit=` -> `slave=` (correct for pymodbus 3.x; pymodbus 4.0 will use `device_id=`);
- `count` is passed as a keyword (it is keyword-only in 3.x);
- read/write failures raise ModbusError instead of returning "error"/-1, so that
  DirectClient can degrade a single failing register to None.
"""
import logging

_LOGGER = logging.getLogger(__name__)

# Framer: FramerType (pymodbus >=3.7) with a fallback to ModbusRtuFramer (older 3.x).
try:
    from pymodbus import FramerType

    RTU_FRAMER = FramerType.RTU
except ImportError:  # pragma: no cover - depends on the pymodbus version
    from pymodbus.transaction import ModbusRtuFramer

    RTU_FRAMER = ModbusRtuFramer


class ModbusError(Exception):
    """The device returned an error response to a register read/write."""


def convert_from_bcd(bcd):
    """Convert a BCD value to decimal (as in app/pyubbink.py)."""
    place, decimal = 1, 0
    while bcd > 0:
        nibble = bcd & 0xF
        decimal += nibble * place
        bcd >>= 4
        place *= 10
    return decimal


_BYPASS_STATUS = {
    0: "initializing",
    1: "opening",
    2: "closing",
    3: "open",
    4: "closed",
}

_AIRFLOW_MODE_FROM_8001 = {0: "holiday", 1: "low", 2: "normal", 3: "high"}
_AIRFLOW_MODE_TO_8001 = {"holiday": 0, "low": 1, "normal": 2, "high": 3}


class VigorDevice:
    """Named read/write commands for the Vigor W325/W400 over a pymodbus client."""

    def __init__(self, client, slave=20):
        self.client = client
        self.slave = slave

    def _read_input(self, address, count=1):
        rr = self.client.read_input_registers(address, count=count, slave=self.slave)
        if rr.isError():
            raise ModbusError(f"read_input_registers {address} failed: {rr}")
        return rr.registers

    def _read_holding(self, address, count=1):
        rr = self.client.read_holding_registers(address, count=count, slave=self.slave)
        if rr.isError():
            raise ModbusError(f"read_holding_registers {address} failed: {rr}")
        return rr.registers

    def _write(self, address, value):
        rr = self.client.write_register(address, value, slave=self.slave)
        if rr.isError():
            raise ModbusError(f"write_register {address}={value} failed: {rr}")

    # --- input registers ---
    def get_serial_number(self):
        regs = self._read_input(4010, count=3)
        return (
            str(convert_from_bcd(regs[0])).zfill(4)
            + str(convert_from_bcd(regs[1])).zfill(4)
            + str(convert_from_bcd(regs[2])).zfill(4)
        )

    def get_supply_pressure(self):
        return self._read_input(4023)[0]

    def get_extract_pressure(self):
        return self._read_input(4024)[0]

    def get_supply_airflow_preset(self):
        return self._read_input(4031)[0]

    def get_supply_airflow_actual(self):
        return self._read_input(4032)[0]

    def get_extract_airflow_preset(self):
        return self._read_input(4041)[0]

    def get_extract_airflow_actual(self):
        return self._read_input(4042)[0]

    def get_supply_temperature(self):
        return self._read_input(4036)[0] / 10.0

    def get_extract_temperature(self):
        return self._read_input(4046)[0] / 10.0

    def get_supply_humidity(self):
        return self._read_input(4037)[0]

    def get_extract_humidity(self):
        return self._read_input(4047)[0]

    def get_bypass_status(self):
        value = self._read_input(4050)[0]
        return _BYPASS_STATUS.get(value, f"unknown ({value})")

    def get_filter_status(self):
        return "dirty" if self._read_input(4100)[0] == 1 else "normal"

    # --- holding registers ---
    def get_airflow_mode(self):
        control = self._read_holding(8000)[0]
        if control == 0:
            return "wall_unit"
        if control == 2:
            return "custom"
        value = self._read_holding(8001)[0]
        return _AIRFLOW_MODE_FROM_8001.get(value, f"unknown ({value})")

    def set_modbus_mode(self, mode):
        """Switch the control mode (8000). Critical: writes are not applied without it."""
        if self._read_holding(8000)[0] != mode:
            self._write(8000, mode)

    def set_airflow_mode(self, mode):
        if mode == "wall_unit":
            self.set_modbus_mode(0)
            return
        if mode not in _AIRFLOW_MODE_TO_8001:
            # "custom" and other modes are not set via 8001 (custom = set a rate via 8002).
            _LOGGER.warning("set_airflow_mode: unsupported mode %r, ignored", mode)
            return
        mode_value = _AIRFLOW_MODE_TO_8001[mode]
        self.set_modbus_mode(1)
        if self._read_holding(8001)[0] != mode_value:
            self._write(8001, mode_value)

    def set_custom_airflow_rate(self, value):
        self.set_modbus_mode(2)
        if value < 50:
            preset = 0
        elif value > 400:
            preset = 400
        else:
            preset = value
        self._write(8002, preset)
