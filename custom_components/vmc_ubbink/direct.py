"""Direct client: Modbus RTU over TCP to a Waveshare RS485-to-ETH gateway.

The interface is identical to ServerClient (api.VMCUbifluxAPI): get_data /
set_airflow_mode / set_airflow_rate / set_bypass_mode — so sensor/number/select
don't care which client they use.
"""
import logging
import threading
import time

from pymodbus.client import ModbusTcpClient

# Relative import inside the HA package; fallback for standalone tests.
try:
    from .vigor import RTU_FRAMER, ModbusError, VigorDevice
except ImportError:  # pragma: no cover - path for tests outside the package
    from vigor import RTU_FRAMER, ModbusError, VigorDevice

_LOGGER = logging.getLogger(__name__)

CACHE_TTL = 5.0  # seconds — same as the ModbusManager cache on the server

# result key -> VigorDevice method name
_READERS = {
    "serial_number": "get_serial_number",
    "supply_temperature": "get_supply_temperature",
    "supply_pressure": "get_supply_pressure",
    "supply_humidity": "get_supply_humidity",
    "supply_airflow_actual": "get_supply_airflow_actual",
    "supply_airflow_preset": "get_supply_airflow_preset",
    "extract_temperature": "get_extract_temperature",
    "extract_pressure": "get_extract_pressure",
    "extract_humidity": "get_extract_humidity",
    "extract_airflow_actual": "get_extract_airflow_actual",
    "extract_airflow_preset": "get_extract_airflow_preset",
    "airflow_mode": "get_airflow_mode",
    "bypass_status": "get_bypass_status",
    "filter_status": "get_filter_status",
}


class DirectClient:
    def __init__(self, host, port, slave, *, _device=None, _clock=time.monotonic):
        self._host = host
        self._port = port
        self._slave = slave
        self._lock = threading.Lock()
        self._clock = _clock
        self._cache = None
        self._cache_ts = 0.0
        if _device is not None:
            # Test path: inject a ready VigorDevice, no real socket.
            self._device = _device
            self._client = None
        else:
            self._client = ModbusTcpClient(
                host, port=port, framer=RTU_FRAMER, timeout=10
            )
            self._device = VigorDevice(self._client, slave=slave)

    def _ensure_connected(self):
        if self._client is not None and not self._client.connected:
            self._client.connect()

    def close(self):
        if self._client is not None:
            self._client.close()

    def _poll(self):
        data = {}
        for key, getter in _READERS.items():
            try:
                data[key] = getattr(self._device, getter)()
            except (ModbusError, IndexError) as err:
                _LOGGER.debug("VMC direct read %s failed: %s", key, err)
                data[key] = None
        return data

    def get_data(self):
        now = self._clock()
        if self._cache is not None and (now - self._cache_ts) < CACHE_TTL:
            return self._cache
        with self._lock:
            now = self._clock()
            if self._cache is not None and (now - self._cache_ts) < CACHE_TTL:
                return self._cache
            try:
                self._ensure_connected()
                data = self._poll()
            except Exception as err:  # noqa: BLE001 - transport failure
                _LOGGER.warning("VMC direct poll failed: %s", err)
                return {"error": str(err)}
            self._cache = data
            self._cache_ts = self._clock()
            return data

    def _set(self, func, *args):
        with self._lock:
            try:
                self._ensure_connected()
                func(*args)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("VMC direct write failed: %s", err)
                return {"error": str(err)}
            finally:
                self._cache = None  # invalidate: next get_data re-reads
        return None

    def set_airflow_mode(self, mode):
        err = self._set(self._device.set_airflow_mode, mode)
        return err or {"status": f"Airflow mode set to {mode}"}

    def set_airflow_rate(self, rate):
        err = self._set(self._device.set_custom_airflow_rate, int(rate))
        return err or {"status": f"Airflow rate set to {rate} m³/h"}

    def set_bypass_mode(self, mode):
        # Interface parity with ServerClient; not supported by the vendored register map.
        _LOGGER.debug("set_bypass_mode(%s) ignored: not supported in direct mode", mode)
        return {"status": "bypass mode not supported in direct mode"}
