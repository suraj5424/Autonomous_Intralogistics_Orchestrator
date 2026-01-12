# app/db/connection.py

import sqlite3
from pathlib import Path

# Absolute path to the database file
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "warehouse.db"

def get_connection():
    """
    Returns a SQLite3 connection to the warehouse.db.
    Ensures the data folder exists.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_database():
    """
    Creates tables if they do not exist.
    """
    from app.db.models import ORDERS_TABLE_CREATE, SENSOR_LOGS_TABLE_CREATE

    with get_connection() as conn:
        conn.execute(ORDERS_TABLE_CREATE)
        conn.execute(SENSOR_LOGS_TABLE_CREATE)
        conn.commit()
