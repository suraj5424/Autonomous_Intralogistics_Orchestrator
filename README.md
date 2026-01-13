# Intralogistics Copilot - Multi-Agent System

A clean, deterministic multi-agent intralogistics copilot for warehouse automation and optimization.

## Overview

This system provides a sophisticated multi-agent architecture for warehouse intralogistics, featuring:

- **Deterministic workflow execution** with clear step-by-step processing
- **Specialized agents** for data management, monitoring, and risk assessment
- **Real-time robot health monitoring** with anomaly detection
- **Intelligent order prioritization** based on risk factors
- **Comprehensive API** for system integration
- **Clean, modular architecture** following best practices

https://github.com/user-attachments/assets/278e09e3-b69e-4046-a46b-78ae79ee6fe9

## 🤖 Agents

### 1. **BaseAgent**
- Foundation for all agents with logging, status tracking, and execution capabilities
- Provides common functionality like unique IDs, timestamps, and error handling

### 2. **DataAgent**
- Responsible for all database operations
- Handles SQL queries, data retrieval, and caching
- Provides methods for fetching orders, sensor data, and inventory

### 3. **MonitoringAgent**
- Monitors robot health using sensor data
- Detects anomalies in temperature and vibration
- Assesses robot health status (HEALTHY/WARNING/CRITICAL)
- Generates comprehensive health reports

### 4. **RiskAssessmentAgent**
- Evaluates order risks based on multiple factors
- Prioritizes orders using deterministic algorithms
- Generates actionable recommendations
- Provides risk distribution analysis

### 5. **IntralogisticsOrchestrator**
- Main coordinator of the multi-agent system
- Executes deterministic 5-step workflow:
  1. Data Collection
  2. Robot Health Monitoring
  3. Risk Assessment
  4. Order Prioritization
  5. Recommendation Generation
- Manages agent lifecycle and coordination
- Provides system diagnostics and health checks

### REST API

Start the API server:

```bash
PS D:\Projects\Autonomous_Intralogistics_Orchestrator> uvicorn app.api.main:app --reload

PS D:\Projects\Autonomous_Intralogistics_Orchestrator> streamlit run app/ui/streamlit_app.py 
```

API Endpoints:

- `GET /health` - System health check
- `GET /system-status` - Current system status
- `GET /orders?limit=10` - Prioritized orders
- `GET /robot-health` - Robot health report
- `GET /risk-analysis` - Detailed risk analysis
- `GET /execute-workflow` - Full workflow execution

## Features

### Deterministic Workflow

The system follows a strict 5-step process:

1. **Data Collection**: Gather orders and sensor data
2. **Robot Health Monitoring**: Detect anomalies and assess health
3. **Risk Assessment**: Evaluate order risks based on multiple factors
4. **Order Prioritization**: Sort orders by urgency and importance
5. **Recommendation Generation**: Provide actionable insights

### Robot Health Monitoring

- **Temperature Anomaly Detection**: Identifies overheating robots
- **Vibration Analysis**: Detects mechanical issues
- **Health Status Classification**: HEALTHY/WARNING/CRITICAL
- **Comprehensive Reporting**: Detailed anomaly breakdowns

### Risk Assessment

- **Multi-Factor Analysis**: Considers order status, robot health, and other factors
- **Priority Scoring**: Assigns numerical priorities to orders
- **Risk Categorization**: HIGH/MEDIUM/LOW risk levels
- **Actionable Recommendations**: Specific suggestions for improvement

## Use Cases

1. **Warehouse Automation**: Real-time monitoring and decision support
2. **Predictive Maintenance**: Early detection of robot issues
3. **Order Prioritization**: Intelligent routing and scheduling
4. **System Integration**: API for warehouse management systems
5. **Analytics Dashboard**: Data-driven insights and reporting

## Future Enhancements

- Machine learning for predictive analytics
- Real-time streaming data processing
- Integration with warehouse execution systems
- Advanced visualization dashboard
- Multi-warehouse coordination

## License

- MIT License
