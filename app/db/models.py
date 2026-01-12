# app/db/models.py

# Table names (used in queries)
ORDERS_TABLE = "orders"
SENSOR_LOGS_TABLE = "sensor_logs"

# SQL statements for creating tables (used in initialization)
ORDERS_TABLE_CREATE = f"""
CREATE TABLE IF NOT EXISTS {ORDERS_TABLE} (
    order_id INTEGER PRIMARY KEY,
    robot_id INTEGER,
    status TEXT,
    items INTEGER,
    created_at TEXT
);
"""

SENSOR_LOGS_TABLE_CREATE = f"""
CREATE TABLE IF NOT EXISTS {SENSOR_LOGS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    robot_id INTEGER,
    motor_temp REAL,
    vibration REAL
);
"""
