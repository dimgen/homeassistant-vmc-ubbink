import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEVICE_PORT = os.getenv("DEVICE_PORT", "/dev/ttyUSB0")
    BAUDRATE = int(os.getenv("BAUDRATE", 19200))
    USERNAME = os.getenv("USERNAME", "admin")
    PASSWORD = os.getenv("PASSWORD", "secret")
    PORT = int(os.getenv("PORT", 8000))
