# app/api/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.intralogistics_orchestrator import IntralogisticsOrchestrator
from app.agents.data_agent import DataAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent

# Initialize FastAPI app
app = FastAPI(
    title="Intralogistics Copilot API",
    description="Multi-agent system for warehouse intralogistics optimization",
    version="1.0.0"
)

# Initialize agents
orchestrator = IntralogisticsOrchestrator()
data_agent = DataAgent()
monitoring_agent = MonitoringAgent()
risk_agent = RiskAssessmentAgent()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intralogistics_api")

class HealthResponse(BaseModel):
    status: str
    agents: Dict[str, Any]
    timestamp: str

class SystemStatusResponse(BaseModel):
    system_status: str
    metadata: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    timestamp: str

class OrderResponse(BaseModel):
    order_id: int
    robot_id: int
    status: str
    items: int
    health_status: str
    order_risk: str
    priority: int

class RobotHealthResponse(BaseModel):
    robot_id: int
    anomaly_count: int
    health_status: str
    temp_anomalies: int
    vibration_anomalies: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and agent statuses."""
    try:
        diagnostic = orchestrator.run_diagnostic()
        return {
            "status": diagnostic["status"],
            "agents": diagnostic["agents"],
            "timestamp": diagnostic["diagnostic_timestamp"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get current system status and recommendations."""
    try:
        results = orchestrator.execute()
        return {
            "system_status": results["system_status"],
            "metadata": results["metadata"],
            "risk_assessment": results["risk_assessment"],
            "recommendations": results["recommendations"],
            "timestamp": results["metadata"]["timestamp"]
        }
    except Exception as e:
        logger.error(f"System status failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders", response_model=List[OrderResponse])
async def get_prioritized_orders(limit: Optional[int] = 10):
    """Get prioritized orders with risk assessment."""
    try:
        results = orchestrator.execute()
        prioritized_orders = results["prioritized_orders"][:limit]

        return [
            {
                "order_id": order["order_id"],
                "robot_id": order["robot_id"],
                "status": order["status"],
                "items": order["items"],
                "health_status": order["health_status"],
                "order_risk": order["order_risk"],
                "priority": order["priority"]
            }
            for order in prioritized_orders
        ]
    except Exception as e:
        logger.error(f"Get orders failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/robot-health", response_model=List[RobotHealthResponse])
async def get_robot_health():
    """Get health status of all robots."""
    try:
        # Get sensor data
        sensor_data = data_agent.fetch_sensor_logs()

        # Generate health report
        health_report = monitoring_agent.get_robot_health_report(sensor_data)

        return health_report
    except Exception as e:
        logger.error(f"Get robot health failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-analysis")
async def get_risk_analysis():
    """Get detailed risk analysis."""
    try:
        results = orchestrator.execute()

        # Get risk summary
        orders_df = orchestrator.data_agent.fetch_orders()
        sensor_df = orchestrator.data_agent.fetch_sensor_logs()

        # Process data through the pipeline
        anomaly_data = orchestrator.monitoring_agent.execute(sensor_df)
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
            orchestrator.monitoring_agent.assess_robot_health
        )

        risk_assessed = orchestrator.risk_agent.execute(orders_with_health)
        risk_summary = orchestrator.risk_agent.get_risk_summary(risk_assessed)

        return {
            "risk_summary": risk_summary,
            "system_status": results["system_status"],
            "timestamp": results["metadata"]["timestamp"]
        }
    except Exception as e:
        logger.error(f"Risk analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/execute-workflow")
async def execute_full_workflow():
    """Execute complete workflow and return all results."""
    try:
        results = orchestrator.execute()
        return results
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
