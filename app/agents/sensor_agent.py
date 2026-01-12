# app/agents/sensor_agent.py


# app/agents/sensor_agent.py
import pandas as pd
import sqlite3
from pathlib import Path
from app.db.connection import get_connection
# Database Connection
# ---------------------------
# Using centralized get_connection from app.db.connection

# ---------------------------
# Fetch Sensor Logs
# ---------------------------
def fetch_sensor_logs(limit: int = None) -> pd.DataFrame:
    """
    Fetch all sensor logs from the database.
    Optionally limit the number of rows.
    """
    conn = get_connection()
    query = "SELECT * FROM sensor_logs"
    if limit:
        query += f" LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------------------
# Anomaly Detection
# ---------------------------
def detect_anomalies(sensor_df: pd.DataFrame, temp_threshold: float = 90.0, vibration_threshold: float = 0.5) -> pd.DataFrame:
    """
    Adds boolean columns to indicate anomalies in temperature and vibration.
    """
    df = sensor_df.copy()
    df["is_temp_anomaly"] = df["motor_temp"] > temp_threshold
    df["is_vibration_anomaly"] = df["vibration"] > vibration_threshold
    df["is_anomaly"] = df["is_temp_anomaly"] | df["is_vibration_anomaly"]
    return df

# ---------------------------
# Fetch Anomalies for a Robot
# ---------------------------
def fetch_robot_anomalies(robot_id: int, temp_threshold: float = 90.0, vibration_threshold: float = 0.5) -> pd.DataFrame:
    """
    Returns all sensor logs for a robot with anomaly flags.
    """
    df = fetch_sensor_logs()
    df_robot = df[df["robot_id"] == robot_id]
    df_robot = detect_anomalies(df_robot, temp_threshold, vibration_threshold)
    return df_robot

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    print("=== Sample Sensor Logs ===")
    df = fetch_sensor_logs(limit=5)
    print(df.to_dict(orient="records"))

    print("\n=== Detect Anomalies ===")
    df_anom = detect_anomalies(df)
    print(df_anom.to_dict(orient="records"))

    print("\n=== Robot 1 Anomalies ===")
    print(fetch_robot_anomalies(1).to_dict(orient="records"))
