# scripts/load_data_to_db.py
import sys
from pathlib import Path

# Add project root to sys.path to allow importing 'app'
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.db.connection import get_connection
from app.db.models import ORDERS_TABLE, SENSOR_LOGS_TABLE, ORDERS_TABLE_CREATE, SENSOR_LOGS_TABLE_CREATE

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.execute(ORDERS_TABLE_CREATE)
    cursor.execute(SENSOR_LOGS_TABLE_CREATE)
    conn.commit()

    # Load CSVs
    # Use absolute paths to ensure files are found regardless of CWD
    data_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    orders_df = pd.read_csv(data_dir / "orders.csv")
    sensor_df = pd.read_csv(data_dir / "sensor_logs.csv")

    orders_df.to_sql("orders", conn, if_exists="replace", index=False)
    sensor_df.to_sql("sensor_logs", conn, if_exists="replace", index=False)

    conn.close()
    print("✅ Data loaded into SQLite database (warehouse.db)")

if __name__ == "__main__":
    main()
