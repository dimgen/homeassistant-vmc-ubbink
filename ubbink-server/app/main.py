import time
import threading
import logging
from fastapi import FastAPI, Depends, Request
from modbus_client import ModbusController
from auth import authenticate

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()


def get_client_ip(request: Request) -> str:
    """
    Extracts the real client IP from proxy/Docker headers or falls back to request.client.host.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    return real_ip if real_ip else request.client.host


class ModbusManager:
    """
    Manages Modbus connections, access throttling, and data caching.
    """

    def __init__(
            self,
            access_interval: float = 5,
            max_wait_time: float = 30,
            cache_interval: float = 5,
    ):
        """
        :param access_interval: Minimum time (s) between consecutive Modbus operations.
        :param max_wait_time: Maximum time (s) to wait for the ability to perform Modbus ops.
        :param cache_interval: Lifetime (s) for cached data before re-fetching.
        """
        self.lock = threading.Lock()
        self.access_interval = access_interval
        self.max_wait_time = max_wait_time
        self.cache_interval = cache_interval

        # Throttling state
        self.last_access_time = 0.0

        # Caching state
        self.last_data_access_time = 0.0
        self.cached_data = {}

    def _wait_for_access(self) -> None:
        """
        Waits until Modbus can be accessed (respecting `access_interval`),
        or raises a timeout if `max_wait_time` is exceeded.
        """
        start_time = time.monotonic()

        while True:
            current_time = time.monotonic()
            time_since_last_access = current_time - self.last_access_time

            if time_since_last_access >= self.access_interval:
                self.last_access_time = current_time
                return

            if (current_time - start_time) > self.max_wait_time:
                raise TimeoutError("Timed out waiting for Modbus access.")

            time.sleep(0.5)

    def get_data(self) -> dict:
        """
        Returns cached data if not expired, otherwise fetches new data from Modbus.
        """
        current_time = time.monotonic()
        time_since_last_data = current_time - self.last_data_access_time

        # Return cached data if it's still valid
        if time_since_last_data < self.cache_interval and self.cached_data:
            return self.cached_data

        # Otherwise, fetch new data from the device
        with self.lock:
            modbus = ModbusController()
            if not modbus.connect():
                return {"error": "Could not connect to device"}

            data = modbus.get_data()
            modbus.disconnect()

        self.cached_data = data
        self.last_data_access_time = current_time
        return data

    def set_airflow_mode(self, mode: str) -> dict:
        """
        Sets the airflow mode on the device, respecting throttling and lock,
        and updates the cache with the newly fetched data.
        """
        self._wait_for_access()
        with self.lock:
            modbus = ModbusController()
            if not modbus.connect():
                return {"error": "Could not connect to device"}

            response = modbus.set_airflow_mode(mode)

            # Fetch fresh data and update cache
            new_data = modbus.get_data()
            modbus.disconnect()

        # Update cached data so subsequent calls reflect the new state
        self.cached_data = new_data
        self.last_data_access_time = time.monotonic()

        return response

    def set_airflow_rate(self, rate: int) -> dict:
        """
        Sets the airflow rate on the device, respecting throttling and lock,
        and updates the cache with the newly fetched data.
        """
        self._wait_for_access()
        with self.lock:
            modbus = ModbusController()
            if not modbus.connect():
                return {"error": "Could not connect to device"}

            response = modbus.set_airflow_rate(rate)

            # Fetch fresh data and update cache
            new_data = modbus.get_data()
            modbus.disconnect()

        # Update cached data so subsequent calls reflect the new state
        self.cached_data = new_data
        self.last_data_access_time = time.monotonic()

        return response


# Instantiate a single manager instance for the entire application
modbus_manager = ModbusManager(
    access_interval=5,
    max_wait_time=30,
    cache_interval=5
)


@app.get("/")
def read_root(request: Request):
    client_ip = get_client_ip(request)
    logger.info(f"📡 Request from {client_ip}: GET /")
    response = {"message": "VMC Ubiflux API is running"}
    logger.info(f"📤 Response to {client_ip}: {response}")
    return response


@app.get("/data", dependencies=[Depends(authenticate)])
def get_device_data(request: Request):
    client_ip = get_client_ip(request)
    logger.info(f"📡 Request from {client_ip}: GET /data")

    data = modbus_manager.get_data()
    logger.info(f"📤 Response to {client_ip}: {data}")
    return data


@app.post("/set_mode", dependencies=[Depends(authenticate)])
@app.get("/set_mode", dependencies=[Depends(authenticate)])
def set_airflow_mode(request: Request, mode: str):
    client_ip = get_client_ip(request)
    logger.info(f"📡 Request from {client_ip}: /set_mode?mode={mode}")

    response = modbus_manager.set_airflow_mode(mode)
    logger.info(f"📤 Response to {client_ip}: {response}")
    return response


@app.post("/set_rate", dependencies=[Depends(authenticate)])
@app.get("/set_rate", dependencies=[Depends(authenticate)])
def set_airflow_rate(request: Request, rate: int):
    client_ip = get_client_ip(request)
    logger.info(f"📡 Request from {client_ip}: /set_rate?rate={rate}")

    response = modbus_manager.set_airflow_rate(rate)
    logger.info(f"📤 Response to {client_ip}: {response}")
    return response