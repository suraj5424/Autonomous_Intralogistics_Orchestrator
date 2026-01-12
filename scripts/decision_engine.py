# scripts/decision_engine.py
import os
import sys
import pandas as pd
from pathlib import Path

# ------------------------
# Path setup for modules
# ------------------------
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.agents.sensor_agent import detect_anomalies
from app.db.connection import get_connection
from app.db.models import ORDERS_TABLE, SENSOR_LOGS_TABLE
from scripts.llm_interface import call_cerebras, print_response_chunks, build_prompt 

LLM_MODE = "cerebras"

# ------------------------
# INFERENCE PARSING
# ------------------------
def parse_llm_action_plan_polished(explanation, row):
    """
    Parse LLM explanation into structured action plan
    """
    lines = [line.strip() for line in explanation.split("\n") if line.strip() != ""]

    # Extract problem
    problem = ""
    for line in lines:
        if any(k in line.lower() for k in ["robot", "anomaly", "issue", "risk", "critical"]):
            problem = line
            break
    if not problem:
        problem = "Check robot and order status"
    problem = problem.replace("**Problem:**", "").replace("**Problem (If Any):**", "").strip()

    # Extract actions
    actions = []
    skip_keywords = ["problem", "why", "next", "based on", "here's", "breakdown", "action:"]
    for line in lines:
        if any(skip in line.lower() for skip in skip_keywords):
            continue
        if len(line) > 10:
            cleaned = line.lstrip("-*0123456789. ").replace("**", "").strip()
            if cleaned and cleaned not in actions:
                actions.append(cleaned)

    if not actions:
        actions = ["Review manually"]

    return {
        "order_id": row.order_id,
        "robot_id": row.robot_id,
        "risk_level": row.order_risk,
        "problem": problem,
        "recommended_actions": actions,
        "next_steps": ["Implement recommended actions"]
    }

# ------------------------
# MAIN
# ------------------------
def main():
    # Load data from SQLite
    conn = get_connection()
    orders_df = pd.read_sql(f"SELECT * FROM {ORDERS_TABLE}", conn)
    sensor_df = pd.read_sql(f"SELECT * FROM {SENSOR_LOGS_TABLE}", conn)

    # Detect anomalies in sensor data
    sensor_df = detect_anomalies(sensor_df)

    # Merge orders and sensor anomalies
    orders_df = orders_df.merge(sensor_df.groupby("robot_id")["is_anomaly"].sum().reset_index(name="anomaly_count"),
                                on="robot_id", how="left")
    orders_df["anomaly_count"] = orders_df["anomaly_count"].fillna(0)

    # Assign robot health
    def robot_health(anomaly_count):
        if anomaly_count == 0:
            return "HEALTHY"
        elif anomaly_count <= 5:
            return "WARNING"
        else:
            return "CRITICAL"
    orders_df["health_status"] = orders_df["anomaly_count"].apply(robot_health)

    # Assign order risk
    def order_risk(row):
        if row["status"] == "DELAYED" and row["health_status"] == "CRITICAL":
            return "HIGH"
        elif row["health_status"] in ["WARNING", "CRITICAL"]:
            return "MEDIUM"
        else:
            return "LOW"
    orders_df["order_risk"] = orders_df.apply(order_risk, axis=1)

    # Sample 5 orders for demo
    polished_final = []
    for _, row in orders_df.sample(5).iterrows():
        prompt = build_prompt(row)

        if LLM_MODE == "cerebras":
            explanation = call_cerebras(prompt)
        else:
            explanation = "[Review manually]"

        plan = parse_llm_action_plan_polished(explanation, row)
        polished_final.append(plan)

    polished_df = pd.DataFrame(polished_final)
    polished_df.to_csv("data/processed/polished_action_plans.csv", index=False)
    print("Structured action plans saved to data/processed/polished_action_plans.csv")
    print(polished_df)

# ------------------------
if __name__ == "__main__":
    main()
