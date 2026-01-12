# app/agents/intralogistics_orchestrator.py

import pandas as pd
from typing import Any, Dict, List, Optional
from app.agents.base_agent import BaseAgent
from app.agents.data_agent import DataAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
import logging

class IntralogisticsOrchestrator(BaseAgent):
    """Main orchestrator for the multi-agent intralogistics copilot system."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id, "IntralogisticsOrchestrator")
        self.data_agent = DataAgent()
        self.monitoring_agent = MonitoringAgent()
        self.risk_agent = RiskAssessmentAgent()

        # Initialize logging
        self.logger = logging.getLogger("IntralogisticsOrchestrator")
        logging.basicConfig(level=logging.INFO)

    def execute(self) -> Dict[str, Any]:
        """
        Execute the complete intralogistics workflow.

        Returns:
            Dictionary containing all results and recommendations
        """
        self.log("Starting intralogistics workflow execution")

        try:
            # Step 1: Data Collection
            self.log("Step 1/5: Collecting data from database")
            orders_df, sensor_df = self._collect_data()

            # Step 2: Robot Health Monitoring
            self.log("Step 2/5: Monitoring robot health")
            health_report, orders_with_health = self._monitor_robot_health(orders_df, sensor_df)

            # Step 3: Risk Assessment
            self.log("Step 3/5: Assessing order risks")
            risk_assessed_orders = self._assess_risks(orders_with_health)

            # Step 4: Order Prioritization
            self.log("Step 4/5: Prioritizing orders")
            prioritized_orders = self._prioritize_orders(risk_assessed_orders)

            # Step 5: Generate Recommendations
            self.log("Step 5/5: Generating recommendations")
            recommendations = self._generate_recommendations(prioritized_orders)

            # Compile final report
            final_report = self._compile_final_report(
                orders_df, sensor_df, health_report,
                prioritized_orders, recommendations
            )

            self.log("Intralogistics workflow completed successfully")
            return final_report

        except Exception as e:
            self.log(f"Workflow failed: {str(e)}", level="error")
            raise

    def _collect_data(self) -> tuple:
        """Collect data from all sources."""
        # Fetch orders data
        orders_df = self.data_agent.fetch_orders()
        self.log(f"Retrieved {len(orders_df)} orders")

        # Fetch sensor data
        sensor_df = self.data_agent.fetch_sensor_logs()
        self.log(f"Retrieved {len(sensor_df)} sensor records")

        return orders_df, sensor_df

    def _monitor_robot_health(self, orders_df: pd.DataFrame, sensor_df: pd.DataFrame) -> tuple:
        """Monitor robot health and merge with orders."""
        # Detect anomalies in sensor data
        anomaly_data = self.monitoring_agent.execute(sensor_df)

        # Generate health report
        health_report = self.monitoring_agent.get_robot_health_report(sensor_df)

        # Merge health data with orders
        robot_anomaly_stats = (
            anomaly_data.groupby("robot_id")["is_anomaly"]
            .sum()
            .reset_index(name="anomaly_count")
        )

        orders_with_health = orders_df.merge(
            robot_anomaly_stats,
            on="robot_id",
            how="left"
        )
        orders_with_health["anomaly_count"] = orders_with_health["anomaly_count"].fillna(0).astype(int)
        orders_with_health["health_status"] = orders_with_health["anomaly_count"].apply(
            self.monitoring_agent.assess_robot_health
        )

        self.log(f"Health monitoring complete for {len(robot_anomaly_stats)} robots")
        return health_report, orders_with_health

    def _assess_risks(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Assess risks for all orders."""
        risk_assessed = self.risk_agent.execute(orders_df)

        # Log risk distribution
        risk_counts = risk_assessed["order_risk"].value_counts().to_dict()
        self.log(f"Risk assessment: {risk_counts}")

        return risk_assessed

    def _prioritize_orders(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Prioritize orders based on risk assessment."""
        prioritized = self.risk_agent.prioritize_orders(orders_df)
        self.log(f"Prioritized {len(prioritized)} orders")
        return prioritized

    def _generate_recommendations(self, orders_df: pd.DataFrame) -> List[str]:
        """Generate actionable recommendations."""
        risk_summary = self.risk_agent.get_risk_summary(orders_df)
        return risk_summary["recommendations"]

    def _compile_final_report(self, orders_df: pd.DataFrame, sensor_df: pd.DataFrame,
                            health_report: List[Dict], prioritized_orders: pd.DataFrame,
                            recommendations: List[str]) -> Dict[str, Any]:
        """Compile comprehensive final report."""
        return {
            "metadata": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "total_orders": len(orders_df),
                "total_sensor_records": len(sensor_df),
                "orchestrator_id": self.agent_id
            },
            "robot_health": health_report,
            "risk_assessment": {
                "distribution": prioritized_orders["order_risk"].value_counts().to_dict(),
                "high_risk_count": len(prioritized_orders[prioritized_orders["order_risk"] == "HIGH"]),
                "medium_risk_count": len(prioritized_orders[prioritized_orders["order_risk"] == "MEDIUM"]),
                "low_risk_count": len(prioritized_orders[prioritized_orders["order_risk"] == "LOW"])
            },
            "prioritized_orders": prioritized_orders.sort_values("priority").to_dict(orient="records"),
            "recommendations": recommendations,
            "system_status": self._assess_system_status(prioritized_orders)
        }

    def _assess_system_status(self, orders_df: pd.DataFrame) -> str:
        """Assess overall system status."""
        high_risk_count = len(orders_df[orders_df["order_risk"] == "HIGH"])
        critical_robots = len(orders_df[orders_df["health_status"] == "CRITICAL"])

        if high_risk_count > 3 or critical_robots > 2:
            return "CRITICAL"
        elif high_risk_count > 0 or critical_robots > 0:
            return "WARNING"
        else:
            return "NORMAL"

    def get_agent_statuses(self) -> Dict[str, Any]:
        """Get status of all agents in the system."""
        return {
            "orchestrator": self.get_status(),
            "data_agent": self.data_agent.get_status(),
            "monitoring_agent": self.monitoring_agent.get_status(),
            "risk_agent": self.risk_agent.get_status()
        }

    def run_diagnostic(self) -> Dict[str, Any]:
        """Run diagnostic check on the system."""
        self.log("Running system diagnostic")

        try:
            # Test data agent
            test_orders = self.data_agent.fetch_orders(limit=5)
            self.log(f"Data agent: OK (retrieved {len(test_orders)} test records)")

            # Test monitoring agent
            test_sensor = self.data_agent.fetch_sensor_logs(limit=10)
            anomaly_test = self.monitoring_agent.execute(test_sensor)
            self.log(f"Monitoring agent: OK (detected {anomaly_test['is_anomaly'].sum()} anomalies in test)")

            # Test risk agent
            test_orders_with_health = test_orders.copy()
            test_orders_with_health["health_status"] = "HEALTHY"
            risk_test = self.risk_agent.execute(test_orders_with_health)
            self.log(f"Risk agent: OK (assessed {len(risk_test)} orders)")

            return {
                "status": "HEALTHY",
                "agents": self.get_agent_statuses(),
                "diagnostic_timestamp": pd.Timestamp.now().isoformat()
            }

        except Exception as e:
            self.log(f"Diagnostic failed: {str(e)}", level="error")
            return {
                "status": "FAILED",
                "error": str(e),
                "diagnostic_timestamp": pd.Timestamp.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    orchestrator = IntralogisticsOrchestrator()
    print("=== Running Intralogistics Orchestrator ===")

    # Run diagnostic first
    diagnostic = orchestrator.run_diagnostic()
    print(f"System Diagnostic: {diagnostic['status']}")

    # Execute full workflow
    results = orchestrator.execute()

    print(f"\n=== System Status: {results['system_status']} ===")
    print(f"Total Orders: {results['metadata']['total_orders']}")
    print(f"Risk Distribution: {results['risk_assessment']['distribution']}")
    print(f"Recommendations: {len(results['recommendations'])} items")

    # Show sample prioritized orders
    print(f"\n=== Top 3 Prioritized Orders ===")
    for i, order in enumerate(results['prioritized_orders'][:3]):
        print(f"{i+1}. Order {order['order_id']} - Risk: {order['order_risk']}, Priority: {order['priority']}")
