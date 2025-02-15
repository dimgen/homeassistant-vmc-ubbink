# VMC Ubbink Ubiflux Vigor Home Assistant Integration

This integration allows you to connect and control your Ubbink Ubiflux Vigor (at least W325 or W400) ventilation system from Home Assistant.

## 📌 Important: Requires Starting a Server (included in this repo) and Connecting it to Ubiflux Device via Modbus RTU
This integration requires a Python server running in a Docker container, which:
- Reads data from the Ubiflux system using Modbus RTU.
- Provides a REST API for Home Assistant to access and control the ventilation system.

The server can be installed on:
- **A separate device** (e.g., NAS, Raspberry Pi, Linux).
- **The same machine where Home Assistant is running** (if it supports Docker).

The server code is based on the [pyubbink](https://github.com/asillye/pyubbink). Please read its documentation for more details, e.g. how to connect to Ubiflux Device via Modbus.

---

## 🚀 **Installation Guide**
### **1️⃣ Install the Ubiflux Server**
To install the server, run the following commands on a device with **Docker & Docker Compose**:

```sh
git clone https://github.com/dimgen/homeassistant-vmc-ubbink.git
cd server
docker-compose up --build -d
```
The server will expose an API on port **8085** by default (configurable via .env).

## 2️⃣ Install the Home Assistant Integration

Option a) **Via HACS**:
1.	Open **HACS** in Home Assistant.
2.	Go to **Integrations** → Click **Custom Repositories**.
3.	Add `https://github.com/dimgen/homeassistant-vmc-ubbink` and select Type **Integration**.
4.	Click **Add**.
5.	Restart Home Assistant.

Option b) **Manual Installation**:

1. Download this repository and place it inside Home Assistant's `custom_components` folder.
2. Restart Home Assistant.

## 🔧 Configuration

## 🔧 **Configuration**
### **1️⃣ Add Integration in Home Assistant**
1. Go to **Settings** → **Devices & Services**.
2. Click **+ Add Integration** → Search for **VMC Ubbink Ubiflux**.
3. Enter the connection details:
- **Server Host** (IP/hostname of the Ubiflux server)
- **Server Port** (default: `8085`)
- **Username & Password** (from `.env` file in server)
4. Click **Submit**.

### **2️⃣ Devices & Controls**
Once added, Home Assistant will recognize **VMC Ubiflux as a single device** with the following features:

#### ✅ **Sensors (Read-only)**
| Name                      | Entity ID                         | Unit |
|---------------------------|----------------------------------|------|
| **Supply Temperature**     | `sensor.vmc_supply_temperature` | °C   |
| **Supply Pressure**        | `sensor.vmc_supply_pressure`    | Pa   |
| **Supply Airflow Actual**  | `sensor.vmc_supply_airflow_actual` | m³/h |
| **Supply Airflow Preset**  | `sensor.vmc_supply_airflow_preset` | m³/h |
| **Extract Temperature**    | `sensor.vmc_extract_temperature` | °C   |
| **Extract Pressure**       | `sensor.vmc_extract_pressure` | Pa   |
| **Extract Airflow Actual** | `sensor.vmc_extract_airflow_actual` | m³/h |
| **Extract Airflow Preset** | `sensor.vmc_extract_airflow_preset` | m³/h |
| **Airflow Mode**           | `sensor.vmc_airflow_mode`      |      |
| **Bypass Status**          | `sensor.vmc_bypass_status`     |      |
| **Filter Status**          | `sensor.vmc_filter_status`     |      |
| **Serial Number**          | `sensor.vmc_serial_number`     |      |

#### ✅ **Controls**
| Name               | Entity ID                 | Type    | Options / Range |
|--------------------|--------------------------|---------|-----------------|
| **Airflow Mode**   | `select.vmc_airflow_mode` | Select  | `wall_unit`, `holiday`, `low`, `normal`, `high` |
| **Airflow Rate**   | `number.vmc_airflow_rate` | Number  | `50-400` m³/h |

---

## 🔍 **Example Dashboard Configuration**
You can add the sensors and controls to your Lovelace dashboard using YAML:

```yaml
type: entities
title: Ventilation System
entities:
- entity: sensor.vmc_supply_temperature
- entity: sensor.vmc_supply_pressure
- entity: sensor.vmc_supply_airflow_actual
- entity: sensor.vmc_extract_temperature
- entity: sensor.vmc_extract_pressure
- entity: sensor.vmc_extract_airflow_actual
- entity: select.vmc_airflow_mode
- entity: number.vmc_airflow_rate
```

## 🛠 Troubleshooting

### Connection Issues
-	Ensure the Ubiflux Server is running and accessible from Home Assistant.
-	Check if the correct host/port is entered in the integration settings.
-	Look at the server logs using:

```sh
docker logs vmc-ubbink-server
```

### Data Not Updating
-	Restart Home Assistant after adding the integration.
-	Check the API response manually:
```sh
curl -u admin:secret http://server-ip:8085/data
```

## 📜 License

This project is licensed under the **MIT License**.

## 👨‍💻 Contributing

Pull requests are welcome! If you find issues, feel free to open an [issue](https://github.com/dimgen/homeassistant-vmc-ubbink/issues).
