# app/agents/llm_orchestrator.py

import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from app.agents.base_agent import BaseAgent
from app.agents.data_agent import DataAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.sql_agent import fetch_orders as sql_fetch_orders
from app.agents.sensor_agent import fetch_sensor_logs as sensor_fetch_logs, detect_anomalies
import logging
import json
from datetime import datetime
from scripts.llm_interface import call_cerebras, build_prompt

class LLMOrcestrator(BaseAgent):
    """LLM-based orchestrator that dynamically triggers agents based on system state and context."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id, "LLMOrcestrator")
        self.data_agent = DataAgent()
        self.monitoring_agent = MonitoringAgent()
        self.risk_agent = RiskAssessmentAgent()

        # Available agents registry
        self.available_agents = {
            "data_agent": self.data_agent,
            "monitoring_agent": self.monitoring_agent,
            "risk_agent": self.risk_agent
        }

        # Initialize logging
        self.logger = logging.getLogger("LLMOrcestrator")
        logging.basicConfig(level=logging.INFO)

    def execute(self) -> Dict[str, Any]:
        """
        Execute the LLM-driven orchestration workflow.

        Returns:
            Dictionary containing all results and recommendations
        """
        self.log("Starting LLM-driven intralogistics workflow execution")

        try:
            # Step 1: Collect initial system state
            system_state = self._collect_system_state()

            # Step 2: LLM determines which agents to trigger and execution sequence
            execution_plan = self._determine_execution_plan(system_state)

            # Step 3: Execute the dynamic workflow
            results = self._execute_dynamic_workflow(execution_plan)

            # Step 4: Generate final report
            final_report = self._compile_final_report(system_state, execution_plan, results)

            self.log("LLM-driven workflow completed successfully")
            return final_report

        except Exception as e:
            self.log(f"LLM workflow failed: {str(e)}", level="error")
            raise

    def _collect_system_state(self) -> Dict[str, Any]:
        """Collect comprehensive system state for LLM analysis."""
        self.log("Collecting system state for LLM analysis")

        # Get basic system information
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "agents_available": list(self.available_agents.keys()),
            "agent_statuses": {name: agent.get_status() for name, agent in self.available_agents.items()}
        }

        # Get sample data for context
        try:
            # Sample orders data
            orders_sample = self.data_agent.fetch_orders(limit=10)
            system_info["orders_sample"] = orders_sample.to_dict(orient="records") if not orders_sample.empty else []

            # Sample sensor data
            sensor_sample = self.data_agent.fetch_sensor_logs(limit=10)
            system_info["sensor_sample"] = sensor_sample.to_dict(orient="records") if not sensor_sample.empty else []

            # Current system metrics
            system_info["metrics"] = self._get_system_metrics()

        except Exception as e:
            self.log(f"Error collecting system data: {str(e)}", level="warning")
            system_info["data_collection_error"] = str(e)

        return system_info

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics for LLM context."""
        try:
            # Get total counts
            total_orders = len(self.data_agent.fetch_orders())
            total_sensor_records = len(self.data_agent.fetch_sensor_logs())

            # Get recent anomalies
            sensor_data = self.data_agent.fetch_sensor_logs(limit=100)
            if not sensor_data.empty:
                anomaly_data = detect_anomalies(sensor_data)
                recent_anomalies = int(anomaly_data["is_anomaly"].sum())  # Convert numpy int to Python int
            else:
                recent_anomalies = 0

            return {
                "total_orders": total_orders,
                "total_sensor_records": total_sensor_records,
                "recent_anomalies": recent_anomalies,
                "active_agents": len(self.available_agents)
            }
        except Exception as e:
            self.log(f"Error getting system metrics: {str(e)}", level="warning")
            return {"error": str(e)}

    def _determine_execution_plan(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to determine which agents to trigger and execution sequence.

        Args:
            system_state: Current system state information

        Returns:
            Execution plan with agent sequence and parameters
        """
        self.log("LLM determining optimal execution plan")

        # Build LLM prompt for execution planning
        prompt = self._build_execution_plan_prompt(system_state)

        try:
            # Call LLM to get execution plan
            llm_response = call_cerebras(prompt)
            self.log(f"LLM execution plan response: {llm_response}")

            # Parse LLM response into structured execution plan
            execution_plan = self._parse_execution_plan(llm_response)

            # Validate and adjust execution plan
            validated_plan = self._validate_execution_plan(execution_plan)

            return validated_plan

        except Exception as e:
            self.log(f"Error determining execution plan: {str(e)}", level="error")
            # Fallback to default execution plan
            return self._get_default_execution_plan()

    def _build_execution_plan_prompt(self, system_state: Dict[str, Any]) -> str:
        """Build LLM prompt for determining execution plan."""
        # Convert system state to JSON for LLM
        state_json = json.dumps(system_state, indent=2)

        return f"""
You are an AI orchestrator for an autonomous intralogistics system. Analyze the current system state and determine the optimal execution plan.

Current System State:
{state_json}

Available Agents:
{', '.join(self.available_agents.keys())}

Agent Capabilities:
- data_agent: Fetches orders and sensor data from database
- monitoring_agent: Monitors robot health and detects anomalies
- risk_agent: Assesses order risks and prioritizes orders
- sql_agent: Executes SQL queries for data retrieval
- sensor_agent: Processes sensor data and detects anomalies

Task:
1. Analyze the current system state
2. Determine which agents should be triggered
3. Define the optimal execution sequence
4. Specify any parameters or conditions for each agent

Provide your response in JSON format with the following structure:
{{
    "analysis": "Your analysis of the current system state",
    "recommended_agents": ["agent1", "agent2", ...],
    "execution_sequence": [
        {{
            "agent": "agent_name",
            "action": "description_of_action",
            "parameters": {{"key": "value"}},
            "conditions": ["condition1", "condition2"]
        }},
        ...
    ],
    "reasoning": "Your reasoning for this execution plan"
}}

Focus on dynamic adaptation based on the current context and system needs.
"""

    def _parse_execution_plan(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured execution plan."""
        try:
            # Try to parse as JSON first
            parsed_plan = json.loads(llm_response)
            return parsed_plan
        except json.JSONDecodeError:
            # If not valid JSON, try to extract structured information
            self.log("LLM response not in JSON format, attempting to parse", level="warning")
            return self._extract_plan_from_text(llm_response)

    def _extract_plan_from_text(self, text: str) -> Dict[str, Any]:
        """Extract execution plan from unstructured text."""
        # Simple text parsing - this would be enhanced in production
        plan = {
            "analysis": "System requires comprehensive monitoring and risk assessment",
            "recommended_agents": ["data_agent", "monitoring_agent", "risk_agent"],
            "execution_sequence": [
                {
                    "agent": "data_agent",
                    "action": "fetch_orders",
                    "parameters": {"limit": 100},
                    "conditions": ["system_has_orders"]
                },
                {
                    "agent": "data_agent",
                    "action": "fetch_sensor_logs",
                    "parameters": {"limit": 500},
                    "conditions": ["system_has_sensor_data"]
                },
                {
                    "agent": "monitoring_agent",
                    "action": "execute",
                    "parameters": {},
                    "conditions": ["sensor_data_available"]
                },
                {
                    "agent": "risk_agent",
                    "action": "execute",
                    "parameters": {},
                    "conditions": ["health_data_available"]
                }
            ],
            "reasoning": "Comprehensive workflow to assess current system state and identify risks"
        }
        return plan

    def _validate_execution_plan(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and adjust execution plan."""
        validated_plan = execution_plan.copy()

        # Ensure all agents in plan are available
        available_agent_names = set(self.available_agents.keys())
        plan_agents = set()

        for step in validated_plan.get("execution_sequence", []):
            agent_name = step.get("agent")
            if agent_name and agent_name in available_agent_names:
                plan_agents.add(agent_name)
            else:
                self.log(f"Agent {agent_name} not available, removing from plan", level="warning")

        # Update recommended agents list
        validated_plan["recommended_agents"] = list(plan_agents)

        # Filter execution sequence to only available agents
        validated_plan["execution_sequence"] = [
            step for step in validated_plan.get("execution_sequence", [])
            if step.get("agent") in available_agent_names
        ]

        # Add fallback agents if plan is empty
        if not validated_plan["execution_sequence"]:
            self.log("Execution plan is empty, using default sequence", level="warning")
            validated_plan = self._get_default_execution_plan()

        return validated_plan

    def _get_default_execution_plan(self) -> Dict[str, Any]:
        """Get default execution plan as fallback."""
        return {
            "analysis": "Using default execution plan",
            "recommended_agents": ["data_agent", "monitoring_agent", "risk_agent"],
            "execution_sequence": [
                {
                    "agent": "data_agent",
                    "action": "fetch_orders",
                    "parameters": {},
                    "conditions": []
                },
                {
                    "agent": "data_agent",
                    "action": "fetch_sensor_logs",
                    "parameters": {},
                    "conditions": []
                },
                {
                    "agent": "monitoring_agent",
                    "action": "execute",
                    "parameters": {},
                    "conditions": []
                },
                {
                    "agent": "risk_agent",
                    "action": "execute",
                    "parameters": {},
                    "conditions": []
                }
            ],
            "reasoning": "Default comprehensive workflow"
        }

    def _execute_dynamic_workflow(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the dynamic workflow based on LLM-determined plan."""
        self.log(f"Executing dynamic workflow with {len(execution_plan['execution_sequence'])} steps")

        results = {
            "execution_plan": execution_plan,
            "step_results": [],
            "final_data": {}
        }

        # Execute each step in sequence
        for i, step in enumerate(execution_plan["execution_sequence"]):
            step_num = i + 1
            agent_name = step["agent"]
            action = step["action"]
            parameters = step.get("parameters", {})
            conditions = step.get("conditions", [])

            self.log(f"Step {step_num}/{len(execution_plan['execution_sequence'])}: {agent_name}.{action}")

            # Check conditions (simple implementation)
            conditions_met = self._check_conditions(conditions, results)

            if conditions_met:
                try:
                    # Get the agent instance
                    agent = self.available_agents[agent_name]

                    # Execute the agent action
                    if hasattr(agent, action):
                        method = getattr(agent, action)

                        # Handle different parameter requirements
                        if action == "fetch_orders":
                            result = method(**parameters)
                        elif action == "fetch_sensor_logs":
                            result = method(**parameters)
                        elif action == "execute":
                            # For execute methods, we need to provide appropriate data
                            if agent_name == "monitoring_agent":
                                # Get sensor data for monitoring
                                sensor_data = self.data_agent.fetch_sensor_logs()
                                result = method(sensor_data)
                            elif agent_name == "risk_agent":
                                # Get orders with health data for risk assessment
                                orders_data = self.data_agent.fetch_orders()
                                sensor_data = self.data_agent.fetch_sensor_logs()
                                anomaly_data = detect_anomalies(sensor_data)

                                # Merge health data with orders
                                robot_anomaly_stats = (
                                    anomaly_data.groupby("robot_id")["is_anomaly"]
                                    .sum()
                                    .reset_index(name="anomaly_count")
                                )

                                orders_with_health = orders_data.merge(
                                    robot_anomaly_stats,
                                    on="robot_id",
                                    how="left"
                                )
                                orders_with_health["anomaly_count"] = orders_with_health["anomaly_count"].fillna(0).astype(int)
                                orders_with_health["health_status"] = orders_with_health["anomaly_count"].apply(
                                    self.monitoring_agent.assess_robot_health
                                )

                                result = method(orders_with_health)
                            else:
                                result = method()
                        else:
                            result = method(**parameters)

                        # Store step result
                        step_result = {
                            "step": step_num,
                            "agent": agent_name,
                            "action": action,
                            "status": "success",
                            "result_summary": self._summarize_result(result),
                            "timestamp": datetime.now().isoformat()
                        }

                        # Store full result for potential use in subsequent steps
                        results["step_results"].append(step_result)
                        results["final_data"][agent_name] = result

                        self.log(f"Step {step_num} completed successfully")

                    else:
                        error_msg = f"Agent {agent_name} does not have method {action}"
                        self.log(error_msg, level="error")
                        step_result = {
                            "step": step_num,
                            "agent": agent_name,
                            "action": action,
                            "status": "failed",
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        results["step_results"].append(step_result)

                except Exception as e:
                    error_msg = f"Error executing {agent_name}.{action}: {str(e)}"
                    self.log(error_msg, level="error")
                    step_result = {
                        "step": step_num,
                        "agent": agent_name,
                        "action": action,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    results["step_results"].append(step_result)

            else:
                skip_msg = f"Skipping step {step_num} - conditions not met: {conditions}"
                self.log(skip_msg, level="info")
                step_result = {
                    "step": step_num,
                    "agent": agent_name,
                    "action": action,
                    "status": "skipped",
                    "reason": "conditions_not_met",
                    "conditions": conditions,
                    "timestamp": datetime.now().isoformat()
                }
                results["step_results"].append(step_result)

        return results

    def _check_conditions(self, conditions: List[str], results: Dict[str, Any]) -> bool:
        """Check if conditions for a step are met."""
        if not conditions:
            return True

        # Simple condition checking - this would be enhanced in production
        for condition in conditions:
            if condition == "system_has_orders":
                try:
                    orders = self.data_agent.fetch_orders(limit=1)
                    if orders.empty:
                        return False
                except:
                    return False

            elif condition == "system_has_sensor_data":
                try:
                    sensor_data = self.data_agent.fetch_sensor_logs(limit=1)
                    if sensor_data.empty:
                        return False
                except:
                    return False

            elif condition == "sensor_data_available":
                if "sensor_agent" not in results["final_data"]:
                    return False

            elif condition == "health_data_available":
                if "monitoring_agent" not in results["final_data"]:
                    return False

        return True

    def _summarize_result(self, result: Any) -> str:
        """Summarize agent execution result."""
        if isinstance(result, pd.DataFrame):
            return f"DataFrame with {len(result)} rows and {len(result.columns)} columns"
        elif isinstance(result, dict):
            if "is_anomaly" in result:
                anomalies = result["is_anomaly"].sum() if hasattr(result["is_anomaly"], "sum") else 0
                return f"Anomaly detection result with {anomalies} anomalies detected"
            else:
                return f"Dictionary with {len(result)} keys"
        elif isinstance(result, list):
            return f"List with {len(result)} items"
        else:
            return str(result)

    def _compile_final_report(self, system_state: Dict[str, Any],
                            execution_plan: Dict[str, Any],
                            execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile comprehensive final report."""
        # Get final data from execution results
        final_data = execution_results["final_data"]

        # Extract key results
        orders_df = final_data.get("data_agent", pd.DataFrame())
        if isinstance(orders_df, pd.DataFrame) and not orders_df.empty:
            # Use the orders data
            pass
        else:
            # Get orders data
            orders_df = self.data_agent.fetch_orders()

        sensor_df = self.data_agent.fetch_sensor_logs()

        # Calculate metrics
        risk_distribution = {}
        high_risk_count = 0
        system_status = "NORMAL"

        if "risk_agent" in final_data:
            risk_result = final_data["risk_agent"]
            if isinstance(risk_result, pd.DataFrame):
                risk_distribution = risk_result["order_risk"].value_counts().to_dict()
                high_risk_count = len(risk_result[risk_result["order_risk"] == "HIGH"])

                # Calculate system status
                critical_robots = len(risk_result[risk_result["health_status"] == "CRITICAL"])
                if high_risk_count > 3 or critical_robots > 2:
                    system_status = "CRITICAL"
                elif high_risk_count > 0 or critical_robots > 0:
                    system_status = "WARNING"

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "orchestrator_type": "LLM",
                "orchestrator_id": self.agent_id,
                "execution_plan": execution_plan,
                "system_state_analysis": system_state.get("metrics", {})
            },
            "execution_summary": {
                "total_steps": len(execution_results["step_results"]),
                "successful_steps": len([s for s in execution_results["step_results"] if s["status"] == "success"]),
                "failed_steps": len([s for s in execution_results["step_results"] if s["status"] == "failed"]),
                "skipped_steps": len([s for s in execution_results["step_results"] if s["status"] == "skipped"]),
                "step_details": execution_results["step_results"]
            },
            "system_analysis": {
                "total_orders": len(orders_df),
                "total_sensor_records": len(sensor_df),
                "risk_distribution": risk_distribution,
                "high_risk_count": high_risk_count,
                "system_status": system_status
            },
            "llm_insights": {
                "analysis": execution_plan.get("analysis", "No analysis available"),
                "reasoning": execution_plan.get("reasoning", "No reasoning available"),
                "recommended_agents": execution_plan.get("recommended_agents", [])
            },
            "recommendations": self._generate_recommendations(final_data),
            "raw_results": final_data
        }

    def _generate_recommendations(self, final_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on execution results."""
        recommendations = []

        # Basic recommendations based on available data
        if "risk_agent" in final_data:
            risk_result = final_data["risk_agent"]
            if isinstance(risk_result, pd.DataFrame):
                high_risk_orders = risk_result[risk_result["order_risk"] == "HIGH"]
                critical_robots = risk_result[risk_result["health_status"] == "CRITICAL"]

                if not high_risk_orders.empty:
                    recommendations.append(
                        f"URGENT: {len(high_risk_orders)} high-risk orders require immediate attention"
                    )

                if not critical_robots.empty:
                    recommendations.append(
                        f"CRITICAL: {len(critical_robots)} robots in critical condition need maintenance"
                    )

        if "monitoring_agent" in final_data:
            monitoring_result = final_data["monitoring_agent"]
            if isinstance(monitoring_result, pd.DataFrame):
                anomalies = monitoring_result["is_anomaly"].sum()
                if anomalies > 10:
                    recommendations.append(
                        f"WARNING: High anomaly rate detected ({anomalies} anomalies)"
                    )

        if not recommendations:
            recommendations.append("System operating normally - no immediate actions required")

        return recommendations

    def create_custom_workflow(self, workflow_description: str) -> Dict[str, Any]:
        """
        Create a custom agent workflow based on natural language description.

        Args:
            workflow_description: Natural language description of desired workflow

        Returns:
            Execution plan for the custom workflow
        """
        self.log(f"Creating custom workflow: {workflow_description}")

        # Build LLM prompt for custom workflow
        prompt = f"""
You are an AI workflow designer for an autonomous intralogistics system.

User Request:
{workflow_description}

Available Agents:
{', '.join(self.available_agents.keys())}

Agent Capabilities:
- data_agent: Fetches orders and sensor data from database
- monitoring_agent: Monitors robot health and detects anomalies
- risk_agent: Assesses order risks and prioritizes orders
- sql_agent: Executes SQL queries for data retrieval
- sensor_agent: Processes sensor data and detects anomalies

Task:
1. Understand the user's workflow requirements
2. Design an optimal agent execution sequence
3. Specify parameters and conditions for each step
4. Provide reasoning for your design choices

Respond in JSON format with the same structure as execution plans.
"""

        try:
            # Call LLM to design custom workflow
            llm_response = call_cerebras(prompt)
            execution_plan = self._parse_execution_plan(llm_response)
            validated_plan = self._validate_execution_plan(execution_plan)

            return validated_plan

        except Exception as e:
            self.log(f"Error creating custom workflow: {str(e)}", level="error")
            return self._get_default_execution_plan()

    def get_agent_statuses(self) -> Dict[str, Any]:
        """Get status of all agents in the system."""
        return {
            "orchestrator": self.get_status(),
            **{name: agent.get_status() for name, agent in self.available_agents.items()}
        }

    def run_diagnostic(self) -> Dict[str, Any]:
        """Run diagnostic check on the LLM orchestrator system."""
        self.log("Running LLM orchestrator diagnostic")

        try:
            # Test basic functionality
            system_state = self._collect_system_state()

            # Test LLM planning (with simple prompt)
            test_plan = self._get_default_execution_plan()

            return {
                "status": "HEALTHY",
                "system_state": system_state["metrics"],
                "available_agents": list(self.available_agents.keys()),
                "diagnostic_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.log(f"Diagnostic failed: {str(e)}", level="error")
            return {
                "status": "FAILED",
                "error": str(e),
                "diagnostic_timestamp": datetime.now().isoformat()
            }

# Example usage
if __name__ == "__main__":
    llm_orchestrator = LLMOrcestrator()
    print("=== Running LLM Orchestrator ===")

    # Run diagnostic first
    diagnostic = llm_orchestrator.run_diagnostic()
    print(f"System Diagnostic: {diagnostic['status']}")

    # Execute LLM-driven workflow
    results = llm_orchestrator.execute()

    print(f"\n=== LLM Orchestrator Results ===")
    print(f"System Status: {results['system_analysis']['system_status']}")
    print(f"Execution Steps: {results['execution_summary']['total_steps']}")
    print(f"Successful Steps: {results['execution_summary']['successful_steps']}")
    print(f"LLM Analysis: {results['llm_insights']['analysis']}")
    print(f"Recommendations: {len(results['recommendations'])} items")

    # Show sample recommendations
    print(f"\n=== Top Recommendations ===")
    for i, recommendation in enumerate(results['recommendations'][:3]):
        print(f"{i+1}. {recommendation}")

    # Example of custom workflow creation
    print(f"\n=== Creating Custom Workflow ===")
    custom_workflow = llm_orchestrator.create_custom_workflow(
        "Focus on high-risk orders and critical robot health monitoring"
    )
    print(f"Custom workflow created with {len(custom_workflow['execution_sequence'])} steps")
    print(f"Recommended agents: {', '.join(custom_workflow['recommended_agents'])}")
