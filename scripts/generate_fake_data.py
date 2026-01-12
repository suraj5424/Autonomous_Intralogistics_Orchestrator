import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from pathlib import Path

# ----------------------------
# Configuration
# ----------------------------
NUM_ROBOTS = 40
NUM_ORDERS = 1500
NUM_SENSOR_RECORDS = 50000

RANDOM_SEED = 42
TEMP_MEAN = 70
TEMP_STD = 5
TEMP_ANOMALY_THRESHOLD = 90
ANOMALY_PROBABILITY = 0.001  # Further reduced from 0.002 to 0.001 to get healthy robots

# Additional sensor configurations
BATTERY_MEAN = 100
BATTERY_STD = 10
HUMIDITY_MEAN = 50
HUMIDITY_STD = 10
MOTOR_LOAD_MEAN = 50
MOTOR_LOAD_STD = 15

# ----------------------------
# Paths
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

DATA_DIR.mkdir(parents=True, exist_ok=True)

ORDERS_PATH = DATA_DIR / "orders.csv"
SENSORS_PATH = DATA_DIR / "sensor_logs.csv"

# ----------------------------
# Reproducibility
# ----------------------------
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

START_TIME = datetime.now()

# ----------------------------
# Generate Orders
# ----------------------------
def generate_orders() -> pd.DataFrame:
    orders = []

    for i in range(1, NUM_ORDERS + 1):
        # Simulate a slight peak in orders during certain hours (e.g., 9am-5pm)
        order_time = START_TIME + timedelta(minutes=i)
        if random.random() < 0.3:  # 30% chance to have an order during peak time
            order_time += timedelta(hours=random.randint(9, 17))  # Random time between 9am and 5pm

        status = random.choices(["PICKED", "IN_PROGRESS", "DELAYED", "COMPLETED"], [0.4, 0.3, 0.2, 0.1])[0]
        items = random.randint(1, 10)
        robot_id = random.randint(1, NUM_ROBOTS)

        # More realistic delay logic: orders created during later times are more likely to be delayed
        if order_time > START_TIME + timedelta(hours=8):  # After 8 hours
            status = "DELAYED" if random.random() < 0.3 else status  # 30% chance of being delayed

        # Simulate status progression over time
        if random.random() < 0.1:  # 10% chance the order has been delayed previously
            status = "IN_PROGRESS" if status == "PICKED" else status

        orders.append({
            "order_id": i,
            "robot_id": robot_id,
            "status": status,
            "items": items,
            "created_at": order_time
        })

    return pd.DataFrame(orders)

# ----------------------------
# Generate Sensor Logs
# ----------------------------
def classify_risk(motor_temp, vibration, battery_level):
    # Risk classification based on the sensor data
    if motor_temp <= 75 and vibration <= 0.3 and battery_level >= 90:
        return "LOW"  # Healthy robot
    elif motor_temp <= 85 and vibration <= 0.5 and battery_level >= 50:
        return "MEDIUM"  # Moderate risk
    else:
        return "HIGH"  # High risk

def generate_sensor_logs() -> pd.DataFrame:
    sensor_logs = []

    for i in range(NUM_SENSOR_RECORDS):
        robot_id = random.randint(1, NUM_ROBOTS)
        motor_temp = np.random.normal(TEMP_MEAN, TEMP_STD)

        # Make anomalies more likely during "heavy load" periods (e.g., peak work hours)
        if random.random() < ANOMALY_PROBABILITY and motor_temp < TEMP_ANOMALY_THRESHOLD:
            motor_temp += random.randint(20, 40)  # Simulate a significant temperature spike

        # Simulate vibration being influenced by temperature
        vibration = np.random.normal(0.3, 0.05) + (motor_temp - TEMP_MEAN) * 0.01  # More vibration with higher temps

        # Battery level could decrease during high load
        battery_level = np.random.normal(BATTERY_MEAN, BATTERY_STD)
        if motor_temp > TEMP_MEAN + 5:  # Battery decreases with higher load/temp
            battery_level -= random.randint(5, 10)

        # Humidity could affect motor performance
        humidity = np.random.normal(HUMIDITY_MEAN, HUMIDITY_STD)

        # Motor load, affected by robot's tasks
        motor_load = np.random.normal(MOTOR_LOAD_MEAN, MOTOR_LOAD_STD)
        if random.random() < 0.2:  # 20% chance to be under higher load
            motor_load += random.randint(10, 30)

        # Avoid negative values for battery and load
        battery_level = max(0, min(100, battery_level))
        motor_load = max(0, min(100, motor_load))

        # Avoid negative vibration values
        vibration = max(0, vibration)

        # Classify the robot's risk level
        risk_level = classify_risk(motor_temp, vibration, battery_level)

        sensor_logs.append({
            "timestamp": START_TIME + timedelta(seconds=i * 10),
            "robot_id": robot_id,
            "motor_temp": round(motor_temp, 2),
            "vibration": round(vibration, 3),
            "battery_level": round(battery_level, 2),
            "humidity": round(humidity, 2),
            "motor_load": round(motor_load, 2),
            "risk_level": risk_level
        })

    return pd.DataFrame(sensor_logs)

# ----------------------------
# Main
# ----------------------------
def main():
    orders_df = generate_orders()
    sensors_df = generate_sensor_logs()

    orders_df.to_csv(ORDERS_PATH, index=False)
    sensors_df.to_csv(SENSORS_PATH, index=False)

    print("✅ Fake warehouse data generated")
    print(f"Orders saved to: {ORDERS_PATH}")
    print(f"Sensor logs saved to: {SENSORS_PATH}")
    print(f"Orders shape: {orders_df.shape}")
    print(f"Sensor logs shape: {sensors_df.shape}")

if __name__ == "__main__":
    main()
