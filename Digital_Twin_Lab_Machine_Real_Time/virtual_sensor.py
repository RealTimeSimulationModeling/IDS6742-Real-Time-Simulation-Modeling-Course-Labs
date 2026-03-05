"""
IDS6742 - Digital Twin Lab: Virtual IoT Sensor Simulator
=================================================================
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import math
import sys
import socket
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — EDIT THESE
# ─────────────────────────────────────────────────────────────────────────────
STUDENT_UCF_ID  = "ab123456"           # Replace with your UCF ID
BROKER_ADDRESS  = "localhost"          # "localhost" or "test.mosquitto.org"
BROKER_PORT     = 1883
PUBLISH_INTERVAL = 1.0                 # seconds between publishes
COURSE_PREFIX   = "ids6742/spring26"

# Derived topics
TOPIC_TELEMETRY = f"{COURSE_PREFIX}/{STUDENT_UCF_ID}/machine1"
TOPIC_STATUS    = f"{COURSE_PREFIX}/{STUDENT_UCF_ID}/machine1/status"
# ─────────────────────────────────────────────────────────────────────────────

# Machine physics
BASE_TEMP       = 72.0
RUNNING_TEMP    = 85.0
IDLE_TEMP       = 65.0
BASE_VIB        = 0.08
RUNNING_VIB     = 0.22

# State machine
STATES = ["RUNNING", "RUNNING", "RUNNING", "RUNNING", "IDLE", "RUNNING", "STOPPED"]
state_index      = 0
state_ticks      = 0
state_durations  = [40, 35, 50, 45, 15, 60, 5]
current_state    = "RUNNING"
thermal_momentum = BASE_TEMP
vib_momentum     = BASE_VIB
message_count    = 0


# ─── Callbacks (VERSION2) ─────────────────────────────────────────────────────

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"  [OK] Connected to broker at {BROKER_ADDRESS}:{BROKER_PORT}")
        print(f"  [OK] Publishing to topic: {TOPIC_TELEMETRY}\n")
    else:
        print(f"  [ERR] Connection failed — reason code: {reason_code}")
        sys.exit(1)


def on_publish(client, userdata, mid, reason_code, properties):
    pass  # silent


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    if reason_code != 0:
        print(f"\n  [WARN] Unexpected disconnect (rc={reason_code}).")


# ─── Physics helpers ──────────────────────────────────────────────────────────

def next_state():
    global state_index, state_ticks, current_state
    state_ticks += 1
    if state_ticks >= state_durations[state_index]:
        state_ticks = 0
        state_index = (state_index + 1) % len(STATES)
        current_state = STATES[state_index]
        print(f"\n  [STATE] Machine transitioned → {current_state}")
    return current_state


def simulate_reading(tick: int) -> dict:
    global thermal_momentum, vib_momentum

    state = next_state()

    # Target temperature
    if state == "RUNNING":
        target_temp = RUNNING_TEMP + random.gauss(0, 1.2)
    elif state == "IDLE":
        target_temp = IDLE_TEMP + random.gauss(0, 0.6)
    else:
        target_temp = BASE_TEMP + random.gauss(0, 0.3)

    thermal_momentum += (target_temp - thermal_momentum) / 8.0
    temperature = round(thermal_momentum + random.gauss(0, 0.4), 2)
    temperature = max(50.0, min(130.0, temperature))

    # Vibration
    if state == "RUNNING":
        vib_target = RUNNING_VIB + 0.03 * math.sin(tick * 0.15)
    elif state == "IDLE":
        vib_target = BASE_VIB + 0.005 * math.sin(tick * 0.4)
    else:
        vib_target = 0.01

    vib_momentum += (vib_target - vib_momentum) / 5.0
    vibration = round(max(0.0, vib_momentum + random.gauss(0, 0.01)), 4)

    # Power draw
    power_map = {"RUNNING": 18.5, "IDLE": 3.2, "STOPPED": 0.1}
    power_kw  = round(power_map[state] + random.gauss(0, 0.3), 2)

    # Spindle RPM
    rpm_map   = {"RUNNING": 3200, "IDLE": 0, "STOPPED": 0}
    spindle_rpm = rpm_map[state] + (random.randint(-50, 50) if state == "RUNNING" else 0)

    return {
        "timestamp":    int(time.time() * 1000),
        "datetime":     datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "sensor_id":    f"MCH_{STUDENT_UCF_ID.upper()}",
        "machine_id":   "machine1",
        "temperature":  temperature,
        "vibration":    vibration,
        "power_kw":     power_kw,
        "spindle_rpm":  spindle_rpm,
        "status":       state,
        "sequence":     message_count + 1
    }


# ─── Pre-flight check ─────────────────────────────────────────────────────────

def check_broker_reachable(host, port, timeout=3):
    """Test TCP connection to broker before starting MQTT client."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.gaierror:
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    global message_count

    print("=" * 60)
    print("  IDS6742 — Virtual IoT Sensor Simulator")
    print("=" * 60)
    print(f"  Student UCF ID : {STUDENT_UCF_ID}")
    print(f"  Broker         : {BROKER_ADDRESS}:{BROKER_PORT}")
    print(f"  Topic          : {TOPIC_TELEMETRY}")
    print(f"  Interval       : {PUBLISH_INTERVAL}s")
    print()

    # Pre-flight check
    print("  [CHECK] Testing broker connectivity...")
    if not check_broker_reachable(BROKER_ADDRESS, BROKER_PORT):
        print(f"  [ERR] Cannot reach {BROKER_ADDRESS}:{BROKER_PORT}")
        print("  [ERR] Is Mosquitto running?")
        if BROKER_ADDRESS == "localhost":
            print("  [HINT] Windows: services.msc → Mosquitto Broker → Start")
            print("  [HINT] macOS:   brew services start mosquitto")
            print("  [HINT] Linux:   sudo systemctl start mosquitto")
        sys.exit(1)
    print("  [OK] Broker is reachable\n")

    # MQTT client setup (VERSION2)
    client_id = f"UCF_Sensor_{STUDENT_UCF_ID}_{int(time.time())}"
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id
    )
    
    client.on_connect    = on_connect
    client.on_publish    = on_publish
    client.on_disconnect = on_disconnect

    # Connect
    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=60)
    except Exception as e:
        print(f"  [ERR] Connection failed: {e}")
        sys.exit(1)

    client.loop_start()
    time.sleep(1.5)  # Wait for connection

    # Check if actually connected
    if not client.is_connected():
        print("  [ERR] MQTT client failed to connect. Check broker and credentials.")
        client.loop_stop()
        sys.exit(1)

    print("  Press Ctrl+C to stop\n")

    try:
        tick = 0
        consecutive_failures = 0
        MAX_FAILURES = 5

        while True:
            if not client.is_connected():
                print(f"  [WARN] Client disconnected. Reconnecting...")
                consecutive_failures += 1
                if consecutive_failures >= MAX_FAILURES:
                    print(f"  [ERR] Max reconnect attempts reached. Exiting.")
                    break
                time.sleep(2)
                continue

            consecutive_failures = 0
            payload = simulate_reading(tick)
            json_payload = json.dumps(payload)

            result = client.publish(TOPIC_TELEMETRY, json_payload, qos=1)
            
            # Wait for publish to complete
            try:
                result.wait_for_publish(timeout=3.0)
                message_count += 1
                tick += 1

                # Console display
                temp_indicator = "🔥" if payload["temperature"] > 90 else (
                                 "❄️ " if payload["temperature"] < 65 else "🌡️ ")
                state_indicator = "🟢" if payload["status"] == "RUNNING" else (
                                  "🟡" if payload["status"] == "IDLE" else "🔴")

                print(
                    f"  [{message_count:>5}] {state_indicator} {payload['status']:<8} | "
                    f"{temp_indicator}{payload['temperature']:>6.2f}°C | "
                    f"Vib: {payload['vibration']:.4f}g | "
                    f"RPM: {payload['spindle_rpm']:>4} | "
                    f"Pwr: {payload['power_kw']:>5.2f}kW"
                )
            except RuntimeError as e:
                print(f"  [WARN] Publish failed: {e}")
                consecutive_failures += 1

            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n  [STOP] Simulation ended. Total messages sent: {message_count}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("  [OK] Disconnected from broker.\n")


if __name__ == "__main__":
    main()