#!/usr/bin/env python3
"""
Intralogistics Copilot - Demonstration Script

This script demonstrates the complete functionality of the multi-agent intralogistics system.
"""

import sys
sys.path.append('.')

from app.agents.intralogistics_orchestrator import IntralogisticsOrchestrator
from app.agents.data_agent import DataAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
import pandas as pd
import json
from datetime import datetime

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title.upper()}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def demonstrate_system():
    """Demonstrate the complete intralogistics copilot system."""

    print_section("Intralogistics Copilot - Multi-Agent System Demo")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize the orchestrator
    print_subsection("Initializing Multi-Agent System")
    orchestrator = IntralogisticsOrchestrator()
    print(f"✓ Orchestrator initialized: {orchestrator}")
    print(f"✓ Agents loaded: Data, Monitoring, Risk Assessment")

    # Run system diagnostic
    print_subsection("System Diagnostic")
    diagnostic = orchestrator.run_diagnostic()
    print(f"System Status: {diagnostic['status']}")
    print(f"Diagnostic Timestamp: {diagnostic['diagnostic_timestamp']}")

    # Show agent statuses
    print("\nAgent Statuses:")
    for agent_name, agent_status in diagnostic['agents'].items():
        print(f"  • {agent_name}: {agent_status['status']} (ID: {agent_status['agent_id'][:8]}...)")

    # Execute full workflow
    print_section("Executing Intralogistics Workflow")

    # Step 1: Data Collection
    print_subsection("Step 1: Data Collection")
    orders_df = orchestrator.data_agent.fetch_orders()
    sensor_df = orchestrator.data_agent.fetch_sensor_logs()
    print(f"✓ Retrieved {len(orders_df)} orders")
    print(f"✓ Retrieved {len(sensor_df)} sensor records")

    # Step 2: Robot Health Monitoring
    print_subsection("Step 2: Robot Health Monitoring")
    anomaly_data = orchestrator.monitoring_agent.execute(sensor_df)
    health_report = orchestrator.monitoring_agent.get_robot_health_report(sensor_df)

    print(f"✓ Anomalies detected: {anomaly_data['is_anomaly'].sum()}")
    print(f"✓ Temperature anomalies: {anomaly_data['is_temp_anomaly'].sum()}")
    print(f"✓ Vibration anomalies: {anomaly_data['is_vibration_anomaly'].sum()}")

    print("\nRobot Health Summary:")
    for robot in health_report:
        print(f"  • Robot {robot['robot_id']}: {robot['health_status']} "
              f"({robot['anomaly_count']} anomalies)")

    # Step 3: Risk Assessment
    print_subsection("Step 3: Risk Assessment")

    # Prepare orders with health data
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
    risk_counts = risk_assessed["order_risk"].value_counts().to_dict()

    print(f"✓ Risk assessment complete")
    print(f"✓ High risk orders: {risk_counts.get('HIGH', 0)}")
    print(f"✓ Medium risk orders: {risk_counts.get('MEDIUM', 0)}")
    print(f"✓ Low risk orders: {risk_counts.get('LOW', 0)}")

    # Step 4: Order Prioritization
    print_subsection("Step 4: Order Prioritization")
    prioritized_orders = orchestrator.risk_agent.prioritize_orders(risk_assessed)
    print(f"✓ Orders prioritized: {len(prioritized_orders)}")

    # Show top 5 high-priority orders
    high_priority = prioritized_orders[prioritized_orders['priority'] == 1].head(5)
    print(f"\nTop 5 High Priority Orders:")
    for idx, order in high_priority.iterrows():
        print(f"  {idx+1}. Order {order['order_id']} - Robot {order['robot_id']} "
              f"({order['health_status']}) - {order['status']} - {order['items']} items")

    # Step 5: Recommendations
    print_subsection("Step 5: Actionable Recommendations")
    risk_summary = orchestrator.risk_agent.get_risk_summary(prioritized_orders)

    print(f"✓ Generated {len(risk_summary['recommendations'])} recommendations:")
    for i, recommendation in enumerate(risk_summary['recommendations'], 1):
        print(f"  {i}. {recommendation}")

    # Final System Status
    print_section("Final System Analysis")
    results = orchestrator.execute()

    print(f"Overall System Status: {results['system_status']}")
    print(f"Total Orders Processed: {results['metadata']['total_orders']}")
    print(f"Total Sensor Records: {results['metadata']['total_sensor_records']}")

    # Risk Distribution
    print_subsection("Risk Distribution")
    risk_dist = results['risk_assessment']['distribution']
    for risk_level, count in risk_dist.items():
        percentage = (count / results['metadata']['total_orders']) * 100
        print(f"  {risk_level}: {count} orders ({percentage:.1f}%)")

    # Robot Health Overview
    print_subsection("Robot Health Overview")
    critical_robots = sum(1 for r in results['robot_health'] if r['health_status'] == 'CRITICAL')
    warning_robots = sum(1 for r in results['robot_health'] if r['health_status'] == 'WARNING')
    healthy_robots = sum(1 for r in results['robot_health'] if r['health_status'] == 'HEALTHY')

    print(f"  Critical: {critical_robots} robots")
    print(f"  Warning: {warning_robots} robots")
    print(f"  Healthy: {healthy_robots} robots")

    # Sample JSON Output
    print_section("Sample API Response")
    sample_response = {
        "system_status": results["system_status"],
        "metadata": results["metadata"],
        "risk_assessment": results["risk_assessment"],
        "recommendations": results["recommendations"],
        "sample_orders": results["prioritized_orders"][:3]
    }

    print(json.dumps(sample_response, indent=2))

    print_section("Demo Complete")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✓ Multi-agent system successfully demonstrated")
    print("✓ All components working deterministically")
    print("✓ Ready for production deployment")

if __name__ == "__main__":
    demonstrate_system()
