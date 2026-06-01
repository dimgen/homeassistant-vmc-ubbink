DOMAIN = "vmc_ubbink"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8085
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "secret"

# VMC connection mode
CONF_MODE = "mode"
MODE_SERVER = "server"
MODE_DIRECT = "direct"

# Direct (Waveshare TCP) parameters
CONF_SLAVE = "slave_id"
DEFAULT_TCP_PORT = 502   # Waveshare TCP port; separate from DEFAULT_PORT = 8085 (HTTP server)
DEFAULT_SLAVE = 20       # VMC Modbus slave address (UNIT in app/pyubbink.py)
