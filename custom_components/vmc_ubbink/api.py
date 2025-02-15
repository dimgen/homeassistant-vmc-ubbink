import requests
from requests.auth import HTTPBasicAuth

class VMCUbifluxAPI:
    def __init__(self, host, port, username, password):
        self.base_url = f"http://{host}:{port}"
        self.auth = HTTPBasicAuth(username, password)

    def get_data(self):
        try:
            response = requests.get(f"{self.base_url}/data", auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def set_airflow_mode(self, mode):
        try:
            response = requests.post(f"{self.base_url}/set_mode?mode={mode}", auth=self.auth, timeout=10)
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def set_airflow_rate(self, rate):
        try:
            response = requests.post(f"{self.base_url}/set_rate?rate={rate}", auth=self.auth, timeout=10)
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
