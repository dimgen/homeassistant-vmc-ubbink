from fastapi import FastAPI, Depends
from modbus_client import ModbusController
from auth import authenticate

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "VMC Ubiflux API is running"}

@app.get("/data", dependencies=[Depends(authenticate)])
def get_device_data():
    modbus = ModbusController()
    if not modbus.connect():
        return {"error": "Could not connect to device"}

    data = modbus.get_data()
    modbus.disconnect()
    return data

@app.post("/set_mode", dependencies=[Depends(authenticate)])
@app.get("/set_mode", dependencies=[Depends(authenticate)])
def set_airflow_mode(mode: str):
    modbus = ModbusController()
    if not modbus.connect():
        return {"error": "Could not connect to device"}

    response = modbus.set_airflow_mode(mode)
    modbus.disconnect()
    return response

@app.post("/set_rate", dependencies=[Depends(authenticate)])
@app.get("/set_rate", dependencies=[Depends(authenticate)])
def set_airflow_rate(rate: int):
    modbus = ModbusController()
    if not modbus.connect():
        return {"error": "Could not connect to device"}

    response = modbus.set_airflow_rate(rate)
    modbus.disconnect()
    return response
