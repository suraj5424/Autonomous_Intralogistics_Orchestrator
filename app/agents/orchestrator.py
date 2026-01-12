# app/agents/orchestrator.py


# app/agents/orchestrator.py
import pandas as pd
from app.agents.sql_agent import fetch_orders
from app.agents.sensor_agent import fetch_sensor_logs, detect_anomalies

# ---------------------------
# Robot Health Assignment
# ---------------------------
def assign_robot_health(anomaly_count: int) -> str:
    """
    Determine health status based on anomaly count.
    """
    if anomaly_count == 0:
        return "HEALTHY"
    elif anomaly_count <= 5:
        return "WARNING"
    else:
        return "CRITICAL"

# ---------------------------
# Order Risk Assignment
# ---------------------------
def assign_order_risk(row: pd.Series) -> str:
    """
    Determine order risk based on order status and robot health.
    """
    if row["status"] == "DELAYED" and row["health_status"] == "CRITICAL":
        return "HIGH"
    elif row["health_status"] in ["WARNING", "CRITICAL"]:
        return "MEDIUM"
    else:
        return "LOW"

# ---------------------------
# Main Orchestration Function
# ---------------------------
def build_decision_df() -> pd.DataFrame:
    """
    Orchestrate SQL and Sensor Agents to produce decision-ready DataFrame.
    """
    # 1️⃣ Fetch orders and sensor logs
    orders_df = fetch_orders()
    sensor_df = fetch_sensor_logs()

    # 2️⃣ Detect anomalies in sensor logs
    sensor_df = detect_anomalies(sensor_df)

    # 3️⃣ Summarize anomalies per robot
    robot_anomaly_stats = (
        sensor_df.groupby("robot_id")["is_anomaly"]
        .sum()
        .reset_index(name="anomaly_count")
    )

    # 4️⃣ Merge robot anomalies into orders
    orders_with_robots = orders_df.merge(
        robot_anomaly_stats,
        on="robot_id",
        how="left"
    )
    orders_with_robots["anomaly_count"] = orders_with_robots["anomaly_count"].fillna(0).astype(int)

    # 5️⃣ Assign robot health
    orders_with_robots["health_status"] = orders_with_robots["anomaly_count"].apply(assign_robot_health)

    # 6️⃣ Assign order risk
    orders_with_robots["order_risk"] = orders_with_robots.apply(assign_order_risk, axis=1)

    return orders_with_robots

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    df_decision = build_decision_df()
    print("=== Sample Decision DataFrame ===")
    print(df_decision.head().to_dict(orient="records"))
