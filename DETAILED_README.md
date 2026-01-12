# Intralogistics Copilot - Multi-Agent System

## 🚀 Overview

The **Intralogistics Copilot** is a deterministic, multi-agent system designed to automate and optimize warehouse operations. It combines data ingestion, robot health monitoring, risk assessment, order prioritization, and recommendation generation into a single, reproducible workflow. The system is exposed via a FastAPI REST interface and a Streamlit UI, enabling both programmatic integration and interactive visualization.

## 📦 Architecture

```
intralogistics-copilot/
├── app/
│   ├── agents/                # Core multi-agent layer
│   │   ├── base_agent.py      # Abstract base class for all agents
│   │   ├── data_agent.py      # Handles DB access & data retrieval
│   │   ├── monitoring_agent.py# Analyses sensor streams, detects anomalies
│   │   ├── risk_assessment_agent.py # Calculates risk scores & categorises orders
│   │   ├── intralogistics_orchestrator.py # Coordinates the deterministic workflow
│   │   ├── llm_orchestrator.py # LLM-based dynamic orchestration
│   │   ├── orchestrator.py    # Generic orchestration utilities (used by CLI scripts)
│   │   ├── sensor_agent.py    # Sensor data processing and anomaly detection
│   │   └── sql_agent.py       # SQL query execution for data retrieval
│   ├── api/                     # FastAPI interface
│   │   └── main.py              # REST API endpoints
│   ├── db/                      # Database layer
│   │   ├─ connection.py         # SQLAlchemy engine & session management
│   │   └─ models.py             # ORM models for orders, sensors, robots, etc.
│   └── ui/                      # User interfaces
│       └── streamlit_app.py     # Interactive dashboard for monitoring & diagnostics
├── data/                        # Data storage
│   ├── warehouse.db             # SQLite database
│   ├── processed/               # Processed data files
│   └── raw/                     # Raw CSV data
│       ├── orders.csv           # Order data
│       └── sensor_logs.csv      # Sensor data
└── scripts/                     # Utility scripts
    ├── decision_engine.py       # CLI driver that invokes the orchestrator
    ├── generate_fake_data.py    # Helper to populate the DB with synthetic data
    ├── llm_interface.py         # LLM integration utilities
    ├── load_data_to_db.py       # Load CSV data into SQLite database
    └── utils.py                 # Shared helper functions
```

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

### 6. **LLMOrcestrator**
- LLM-based orchestrator that dynamically triggers agents based on system state and context
- Uses Cerebras LLM to determine optimal execution plans
- Provides custom workflow creation based on natural language descriptions
- Offers dynamic adaptation to changing system conditions

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/intralogistics-copilot.git
cd intralogistics-copilot

# Install dependencies
pip install -r requirements.txt

# Run the system
python test_orchestrator.py
```

## 🚀 Usage

### Command Line Interface

```python
from app.agents.intralogistics_orchestrator import IntralogisticsOrchestrator

# Initialize orchestrator
orchestrator = IntralogisticsOrchestrator()

# Run system diagnostic
diagnostic = orchestrator.run_diagnostic()
print(f"System Status: {diagnostic['status']}")

# Execute full workflow
results = orchestrator.execute()
print(f"System Status: {results['system_status']}")
print(f"Recommendations: {results['recommendations']}")
```

### REST API

Start the API server:

```bash
python app/api/main.py
```

API Endpoints:
- `GET /health` - System health check
- `GET /system-status` - Current system status
- `GET /orders?limit=10` - Prioritized orders
- `GET /robot-health` - Robot health report
- `GET /risk-analysis` - Detailed risk analysis
- `GET /execute-workflow` - Full workflow execution

### Streamlit UI

Run the interactive dashboard:

```bash
streamlit run app/ui/streamlit_app.py
```

## 📊 Features

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

### LLM Integration

- **Dynamic Orchestration**: LLM determines optimal agent execution sequence
- **Custom Workflow Creation**: Natural language interface for workflow design
- **Context-Aware Decision Making**: LLM analyzes system state for intelligent recommendations

## 🔍 Example Output

```json
{
  "system_status": "CRITICAL",
  "metadata": {
    "total_orders": 500,
    "total_sensor_records": 2000,
    "timestamp": "2026-01-11T19:34:07.123456"
  },
  "risk_assessment": {
    "distribution": {"HIGH": 169, "MEDIUM": 331, "LOW": 0},
    "high_risk_count": 169,
    "medium_risk_count": 331
  },
  "recommendations": [
    "Immediately address 169 high-risk orders with critical robot issues",
    "Review 331 medium-risk orders for potential delays"
  ],
  "robot_health": [
    {"robot_id": 1, "health_status": "CRITICAL", "anomaly_count": 8},
    {"robot_id": 2, "health_status": "CRITICAL", "anomaly_count": 25}
  ]
}
```

## 🧪 Testing

Run the test suite:

```bash
python test_orchestrator.py
python test_api.py
```

## 📈 Performance

- **Processing Speed**: 500 orders analyzed in < 2 seconds
- **Scalability**: Handles 2000+ sensor records efficiently
- **Deterministic**: Consistent results across multiple runs
- **Reliability**: Comprehensive error handling and logging

## 🎯 Use Cases

1. **Warehouse Automation**: Real-time monitoring and decision support
2. **Predictive Maintenance**: Early detection of robot issues
3. **Order Prioritization**: Intelligent routing and scheduling
4. **System Integration**: API for warehouse management systems
5. **Analytics Dashboard**: Data-driven insights and reporting

## 🔮 Future Enhancements

- Machine learning for predictive analytics
- Real-time streaming data processing
- Integration with warehouse execution systems
- Advanced visualization dashboard
- Multi-warehouse coordination

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please follow the existing code style and submit pull requests.

---

**Intralogistics Copilot** - Transforming warehouse operations with intelligent automation 🚀
