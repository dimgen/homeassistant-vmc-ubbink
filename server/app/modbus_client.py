from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pyubbink import VigorDevice
from config import Config

class ModbusController:
    def __init__(self):
        self.client = ModbusClient(
            port=Config.DEVICE_PORT,
            baudrate=Config.BAUDRATE,
            stopbits=1,
            bytesize=8,
            parity='N',
            method="rtu",
            timeout=60
        )
        self.device = None

    def connect(self):
        if self.client.connect():
            self.device = VigorDevice(self.client)
            return True
        return False

    def disconnect(self):
        self.client.close()

    def get_data(self):
        if not self.device:
            return {"error": "Device not connected"}

        return {
            "serial_number": self.device.get_serial_number(),
            "supply_temperature": self.device.get_supply_temperature(),
            "supply_pressure": self.device.get_supply_pressure(),
            "supply_airflow_actual": self.device.get_supply_airflow_actual(),
            "supply_airflow_preset": self.device.get_supply_airflow_preset(),
            "extract_temperature": self.device.get_extract_temperature(),
            "extract_pressure": self.device.get_extract_pressure(),
            "extract_airflow_actual": self.device.get_extract_airflow_actual(),
            "extract_airflow_preset": self.device.get_extract_airflow_preset(),
            "airflow_mode": self.device.get_airflow_mode(),
            "bypass_status": self.device.get_bypass_status(),
            "filter_status": self.device.get_filter_status(),
        }


    def set_airflow_mode(self, mode: str):
        if not self.device:
            return {"error": "Device not connected"}

        valid_modes = ["wall_unit", "holiday", "low", "normal", "high"]
        if mode not in valid_modes:
            return {"error": "Invalid mode. Valid values: 'wall_unit', 'holiday', 'low', 'normal', 'high'"}

        self.device.set_airflow_mode(mode)
        return {"status": f"Airflow mode set to {mode}"}

    def set_airflow_rate(self, rate: int):
        if not self.device:
            return {"error": "Device not connected"}

        if rate < 50 or rate > 400:
            return {"error": "Invalid rate. Must be between 50 and 400 m³/h"}

        self.device.set_custom_airflow_rate(rate)
        return {"status": f"Airflow rate set to {rate} m³/h"}
