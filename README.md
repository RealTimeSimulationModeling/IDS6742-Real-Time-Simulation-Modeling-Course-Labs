# Lab 8-9: Digital Twin with Real-Time IoT Integration

**Course:** IDS 6742 — Real-Time Simulation Modeling for Digital Twins
**Instructor:** Bulent Soykan ([soykanb@gmail.com](mailto:soykanb@gmail.com))
**Repository:** [IDS6742-Real-Time-Simulation-Modeling-Course-Labs](https://github.com/RealTimeSimulationModeling/IDS6742-Real-Time-Simulation-Modeling-Course-Labs)

---

## Overview

This lab introduces bi-directional real-time communication between IoT sensors, a web-based control interface, and an AnyLogic Digital Twin model using the **MQTT protocol**. Students implement a live digital twin of an industrial machine that receives telemetry from a virtual sensor, visualizes machine state in AnyLogic, and accepts speed commands from a browser-based control panel.

The lab is split into two parts:

| Part | Folder | Focus |
|------|--------|-------|
| Lab | `Digital_Twin_Lab_Machine_Real_Time/` | Live sensor streaming + real-time Digital Twin |
| Lab | `Digital_Twin_Lab_Historical_Data/` | Historical data replay + database-driven Digital Twin |

---

## Architecture

```
[virtual_sensor.py]          [speed_controller.html]
  Python IoT Simulator   <-->   Browser Control Panel
         |                              |
         |         MQTT (pub/sub)       |
         +----------[Mosquitto]---------+
                        |
               [AnyLogic Digital Twin]
                (.alp simulation model)
                        |
                  [HSQLDB Database]
```

**MQTT Topic Structure:**

| Topic | Direction | Description |
|-------|-----------|-------------|
| `ids6742/spring26/{UCF_ID}/machine1` | Sensor → AnyLogic | Machine telemetry (temp, vibration, power, RPM) |
| `ids6742/spring26/{UCF_ID}/machine1/status` | Sensor → AnyLogic | Machine state (RUNNING / IDLE / STOPPED) |
| `ids6742/spring26/{UCF_ID}/speed` | Browser → AnyLogic | Spindle speed setpoint (RPM) |

---

## Prerequisites

- [AnyLogic](https://www.anylogic.com/) (University or Professional edition)
- [Mosquitto MQTT Broker](https://mosquitto.org/download/)
- Python 3.8+ with `paho-mqtt` library
- A modern web browser

Install Python dependency:

```bash
pip install paho-mqtt
```

---

## Setup: Mosquitto Broker

The provided `mosquitto.conf` configures the broker with:
- **Port 1883** — standard MQTT (used by `virtual_sensor.py` and AnyLogic)
- **Port 8083** — WebSocket MQTT (used by the browser-based speed controller)

### Step 1: Copy the config

Place `mosquitto.conf` in your Mosquitto installation directory and start the broker:

```bash
# Windows (run as Administrator or via services.msc)
mosquitto -c "C:\Program Files\mosquitto\mosquitto.conf"

# macOS
brew services start mosquitto
# or: mosquitto -c /path/to/mosquitto.conf

# Linux
sudo systemctl start mosquitto
```

> **Note:** On Windows, edit `mosquitto.conf` to update the `persistence_location` and `log_dest` paths to match your system.

---

## Lab 8: Real-Time Digital Twin

### Files

| File | Description |
|------|-------------|
| `Digital_Twin_Lab.alp` | AnyLogic simulation model |
| `virtual_sensor.py` | Virtual IoT sensor (Python) |
| `speed_controller.html` | Browser-based machine speed controller |
| `mosquitto.conf` | Mosquitto broker configuration |
| `json-20210307.jar` | JSON library for AnyLogic |
| `org.eclipse.paho.client.mqttv3-1.2.5.jar` | Paho MQTT client for AnyLogic |

### Step 2: Run the Virtual Sensor

Open `virtual_sensor.py` and set your UCF ID:

```python
STUDENT_UCF_ID = "ab123456"   # Replace with your UCF ID
```

Then run:

```bash
python virtual_sensor.py
```

The sensor publishes JSON telemetry once per second. The machine cycles through states automatically:

| State | Temperature | Vibration | Power | RPM |
|-------|-------------|-----------|-------|-----|
| RUNNING | ~85°C | ~0.22g | ~18.5 kW | ~3200 |
| IDLE | ~65°C | ~0.08g | ~3.2 kW | 0 |
| STOPPED | ~72°C | ~0.01g | ~0.1 kW | 0 |

**Sample payload:**
```json
{
  "timestamp": 1709123456789,
  "datetime": "2026-03-05T14:30:00",
  "sensor_id": "MCH_AB123456",
  "machine_id": "machine1",
  "temperature": 84.72,
  "vibration": 0.2187,
  "power_kw": 18.23,
  "spindle_rpm": 3175,
  "status": "RUNNING",
  "sequence": 42
}
```

### Step 3: Open the AnyLogic Model

1. Open `Digital_Twin_Lab.alp` in AnyLogic.
2. Ensure the JAR libraries (`json-20210307.jar`, `org.eclipse.paho.client.mqttv3-1.2.5.jar`) are included in the model's classpath (they are bundled in the folder).
3. Run the simulation. The model subscribes to the MQTT telemetry topic and updates the digital twin in real time.

### Step 4: Use the Speed Controller (Optional)

Open `speed_controller.html` in any web browser. Enter your UCF ID, set the broker host to `localhost` and WebSocket port to `8083`, then click **Connect**.

Use the slider or preset buttons to send speed commands to the AnyLogic simulation:
- **IDLE** — 0 RPM
- **MED** — 1600 RPM
- **HIGH** — 3200 RPM
- **E-STOP** — immediate stop signal

---

## Lab 9: Historical Data Digital Twin

### Files

| File | Description |
|------|-------------|
| `Digital_Twin_Lab2.alp` | AnyLogic simulation model (historical replay) |
| `sensor_log_historical.xlsx` | Historical sensor readings |
| `database/` | Embedded HSQLDB database (pre-populated) |
| `json-20210307.jar` | JSON library for AnyLogic |
| `org.eclipse.paho.client.mqttv3-1.2.5.jar` | Paho MQTT client for AnyLogic |

### Database Schema

The embedded HSQLDB database (`sensor_log_db` table) stores:

| Column | Type | Description |
|--------|------|-------------|
| `AL_ID` | INTEGER (PK) | Auto-generated row ID |
| `TIMESTAMP` | TIMESTAMP | Reading time |
| `MACHINE_ID` | VARCHAR | Machine identifier |
| `TEMPERATURE` | DOUBLE | Temperature in °C |
| `VIBRATION_LEVEL` | DOUBLE | Vibration in g |
| `STATUS` | VARCHAR | Machine state |

### Steps

1. Open `Digital_Twin_Lab2.alp` in AnyLogic.
2. The model reads from the HSQLDB database and/or the Excel file to replay historical machine behavior.
3. Run the simulation to observe how the digital twin reconstructs past machine states from logged data.

---

## Troubleshooting

**"Cannot reach localhost:1883" (virtual_sensor.py)**
- Mosquitto is not running. Start it using the commands above.
- Verify no firewall is blocking port 1883.

**"Connection failed" (speed_controller.html)**
- Check Mosquitto is running with WebSocket support (port 8083).
- Your `mosquitto.conf` must include the `listener 8083 / protocol websockets` block.
- Restart Mosquitto after any config changes.

**AnyLogic model not receiving data**
- Confirm `STUDENT_UCF_ID` in `virtual_sensor.py` matches the UCF ID configured in the AnyLogic model.
- Ensure the JAR files are on the AnyLogic model classpath.

---

## Learning Objectives

By completing this lab, students will be able to:

1. Set up and configure an MQTT broker for IoT communication.
2. Implement a Python-based virtual IoT sensor that publishes structured telemetry.
3. Build a bi-directional Digital Twin in AnyLogic that consumes real-time MQTT data.
4. Design a browser-based control interface that sends commands to a running simulation.
5. Compare real-time simulation with historical data replay approaches for Digital Twins.
