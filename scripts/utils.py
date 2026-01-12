# scripts/utils.py
import pandas as pd

def merge_orders_sensors(orders_df, sensor_df):
    robot_anomaly_stats = (
        sensor_df.groupby("robot_id")["is_anomaly"].sum()
        .reset_index(name="anomaly_count")
    )

    orders_with_robots = orders_df.merge(
        robot_anomaly_stats,
        on="robot_id",
        how="left"
    )
    orders_with_robots["anomaly_count"] = orders_with_robots["anomaly_count"].fillna(0)
    return orders_with_robots

def assign_robot_health(anomaly_count):
    if anomaly_count == 0:
        return "HEALTHY"
    elif anomaly_count <= 5:
        return "WARNING"
    else:
        return "CRITICAL"

def assign_order_risk(row):
    if row["status"] == "DELAYED" and row["health_status"] == "CRITICAL":
        return "HIGH"
    elif row["health_status"] in ["WARNING", "CRITICAL"]:
        return "MEDIUM"
    else:
        return "LOW"
