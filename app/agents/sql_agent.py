# app/agents/sql_agent.py


# app/agents/sql_agent.py
import sqlite3
import pandas as pd
from pathlib import Path
from app.db.connection import get_connection
# Database Connection
# ---------------------------
# Using centralized get_connection from app.db.connection

# ---------------------------
# Fetch Orders
# ---------------------------
def fetch_orders(limit: int = None) -> pd.DataFrame:
    """
    Returns all orders as a DataFrame.
    Optionally limit the number of rows.
    """
    conn = get_connection()
    query = "SELECT * FROM orders"
    if limit:
        query += f" LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def fetch_order_by_id(order_id: int) -> pd.DataFrame:
    """
    Returns a single order by ID.
    """
    conn = get_connection()
    query = "SELECT * FROM orders WHERE order_id = ?"
    df = pd.read_sql_query(query, conn, params=(order_id,))
    conn.close()
    return df

def fetch_delayed_orders() -> pd.DataFrame:
    """
    Returns all orders with status = 'DELAYED'.
    """
    conn = get_connection()
    query = "SELECT * FROM orders WHERE status = 'DELAYED'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------------------
# Fetch Inventory
# ---------------------------
def fetch_inventory() -> pd.DataFrame:
    """
    Returns the inventory table from the database.
    """
    conn = get_connection()
    query = "SELECT * FROM inventory"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    print("=== Sample Orders ===")
    print(fetch_orders(limit=5).to_dict(orient="records"))

    print("\n=== Delayed Orders ===")
    print(fetch_delayed_orders().to_dict(orient="records"))
