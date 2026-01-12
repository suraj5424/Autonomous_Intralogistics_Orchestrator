# app/agents/monitoring_agent.py

import pandas as pd
from typing import Any, Dict, List, Optional
from app.agents.base_agent import BaseAgent

class MonitoringAgent(BaseAgent):
    """Agent responsible for monitoring robot health and detecting anomalies."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id, "MonitoringAgent")
        self.temp_threshold = 90.0
        self.vibration_threshold = 0.5

    def execute(self, sensor_data: pd.DataFrame) -> pd.DataFrame:
        """
        Execute anomaly detection on sensor data.

        Args:
            sensor_data: DataFrame containing sensor logs

        Returns:
            DataFrame with anomaly flags added
        """
        return self.detect_anomalies(sensor_data)

    def detect_anomalies(self, sensor_df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies in sensor data based on thresholds.

        Args:
            sensor_df: DataFrame containing sensor logs

        Returns:
            DataFrame with anomaly columns added
        """
        self.log(f"Detecting anomalies in {len(sensor_df)} sensor records")

        df = sensor_df.copy()

        # Temperature anomalies
        df["is_temp_anomaly"] = df["motor_temp"] > self.temp_threshold
        temp_anomalies = df["is_temp_anomaly"].sum()
        self.log(f"Found {temp_anomalies} temperature anomalies")

        # Vibration anomalies
        df["is_vibration_anomaly"] = df["vibration"] > self.vibration_threshold
        vibration_anomalies = df["is_vibration_anomaly"].sum()
        self.log(f"Found {vibration_anomalies} vibration anomalies")

        # Overall anomaly flag
        df["is_anomaly"] = df["is_temp_anomaly"] | df["is_vibration_anomaly"]
        total_anomalies = df["is_anomaly"].sum()
        self.log(f"Total anomalies detected: {total_anomalies}")

        return df

    def assess_robot_health(self, anomaly_count: int) -> str:
        """
        Assess robot health based on anomaly count.

        Args:
            anomaly_count: Number of anomalies detected

        Returns:
            Health status string
        """
        if anomaly_count == 0:
            return "HEALTHY"
        elif anomaly_count <= 2:  # Reduced from 5 to 2 for more realistic distribution
            return "WARNING"
        else:
            return "CRITICAL"

    def get_robot_health_report(self, sensor_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive health report for robots.

        Args:
            sensor_data: DataFrame containing sensor logs

        Returns:
            Dictionary with health assessment
        """
        anomaly_data = self.detect_anomalies(sensor_data)

        # Group by robot and count anomalies
        robot_stats = (
            anomaly_data.groupby("robot_id")["is_anomaly"]
            .sum()
            .reset_index(name="anomaly_count")
        )

        # Add health status
        robot_stats["health_status"] = robot_stats["anomaly_count"].apply(self.assess_robot_health)

        # Add detailed anomaly breakdown
        temp_stats = (
            anomaly_data.groupby("robot_id")["is_temp_anomaly"]
            .sum()
            .reset_index(name="temp_anomalies")
        )
        vibration_stats = (
            anomaly_data.groupby("robot_id")["is_vibration_anomaly"]
            .sum()
            .reset_index(name="vibration_anomalies")
        )

        # Merge all statistics
        health_report = robot_stats.merge(temp_stats, on="robot_id").merge(vibration_stats, on="robot_id")

        self.log(f"Generated health report for {len(health_report)} robots")
        return health_report.to_dict(orient="records")
