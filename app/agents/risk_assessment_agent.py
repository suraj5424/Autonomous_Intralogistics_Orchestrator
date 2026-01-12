# app/agents/risk_assessment_agent.py

import pandas as pd
from typing import Any, Dict, List, Optional
from app.agents.base_agent import BaseAgent

class RiskAssessmentAgent(BaseAgent):
    """Agent responsible for assessing order risks and prioritization."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id, "RiskAssessmentAgent")

    def execute(self, orders_data: pd.DataFrame) -> pd.DataFrame:
        """
        Execute risk assessment on orders data.

        Args:
            orders_data: DataFrame containing orders with health status

        Returns:
            DataFrame with risk assessment added
        """
        return self.assess_order_risks(orders_data)

    def assess_order_risks(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Assess risks for all orders based on status and robot health.

        Args:
            orders_df: DataFrame containing orders with health_status column

        Returns:
            DataFrame with risk assessment added
        """
        self.log(f"Assessing risks for {len(orders_df)} orders")

        df = orders_df.copy()

        # Apply risk assessment logic
        df["order_risk"] = df.apply(self._calculate_order_risk, axis=1)

        # Count risk levels
        risk_counts = df["order_risk"].value_counts().to_dict()
        self.log(f"Risk assessment complete: {risk_counts}")

        return df

    def _calculate_order_risk(self, row: pd.Series) -> str:
        """
        Calculate risk level for a single order.

        Args:
            row: Series containing order data

        Returns:
            Risk level string
        """
        status = row.get("status", "")
        health_status = row.get("health_status", "")

        # High risk: delayed orders with critical robot health
        if status == "DELAYED" and health_status == "CRITICAL":
            return "HIGH"

        # Medium risk: any order with warning or critical robot health
        elif health_status in ["WARNING", "CRITICAL"]:
            return "MEDIUM"

        # Medium risk: delayed orders regardless of robot health
        elif status == "DELAYED":
            return "MEDIUM"

        # Low risk: all other cases
        else:
            return "LOW"

    def prioritize_orders(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prioritize orders based on risk assessment.

        Args:
            orders_df: DataFrame containing orders with risk assessment

        Returns:
            DataFrame sorted by priority
        """
        self.log("Prioritizing orders based on risk assessment")

        # Define priority mapping
        priority_mapping = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}

        df = orders_df.copy()
        df["priority"] = df["order_risk"].map(priority_mapping)

        # Sort by priority, then by items (larger orders first)
        prioritized_df = df.sort_values(["priority", "items"], ascending=[True, False])

        self.log(f"Prioritized {len(prioritized_df)} orders")
        return prioritized_df

    def get_risk_summary(self, orders_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate risk assessment summary.

        Args:
            orders_df: DataFrame containing orders with risk assessment

        Returns:
            Dictionary with risk summary statistics
        """
        risk_counts = orders_df["order_risk"].value_counts().to_dict()

        # Calculate percentages
        total_orders = len(orders_df)
        risk_percentages = {risk: (count / total_orders * 100) for risk, count in risk_counts.items()}

        return {
            "total_orders": total_orders,
            "risk_distribution": risk_counts,
            "risk_percentages": risk_percentages,
            "high_risk_orders": orders_df[orders_df["order_risk"] == "HIGH"].to_dict(orient="records"),
            "recommendations": self._generate_recommendations(risk_counts)
        }

    def _generate_recommendations(self, risk_counts: Dict[str, int]) -> List[str]:
        """Generate recommendations based on risk distribution."""
        recommendations = []

        high_risk = risk_counts.get("HIGH", 0)
        medium_risk = risk_counts.get("MEDIUM", 0)

        if high_risk > 0:
            recommendations.append(f"Immediately address {high_risk} high-risk orders with critical robot issues")

        if medium_risk > 5:
            recommendations.append(f"Review {medium_risk} medium-risk orders for potential delays")

        if high_risk == 0 and medium_risk == 0:
            recommendations.append("All orders are low risk - system operating normally")

        return recommendations
