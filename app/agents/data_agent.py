# app/agents/data_agent.py

import pandas as pd
from typing import Any, Dict, List, Optional, Union
from app.agents.base_agent import BaseAgent
from app.db.connection import get_connection

class DataAgent(BaseAgent):
    """Agent responsible for data retrieval and management."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id, "DataAgent")

    def execute(self, query: str, params: Optional[tuple] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            query: SQL query to execute
            params: Parameters for the query
            limit: Maximum number of rows to return

        Returns:
            DataFrame containing query results
        """
        self.log(f"Executing query: {query[:50]}...")
        conn = get_connection()

        try:
            if limit:
                query = f"SELECT * FROM ({query}) LIMIT {limit}"
            df = pd.read_sql_query(query, conn, params=params)
            self.log(f"Retrieved {len(df)} rows")
            return df
        except Exception as e:
            self.log(f"Query failed: {str(e)}", level="error")
            raise
        finally:
            conn.close()

    def fetch_orders(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetch orders from database."""
        query = "SELECT * FROM orders"
        return self.execute(query, limit=limit)

    def fetch_order_by_id(self, order_id: int) -> pd.DataFrame:
        """Fetch specific order by ID."""
        query = "SELECT * FROM orders WHERE order_id = ?"
        return self.execute(query, params=(order_id,))

    def fetch_delayed_orders(self) -> pd.DataFrame:
        """Fetch delayed orders."""
        query = "SELECT * FROM orders WHERE status = 'DELAYED'"
        return self.execute(query)

    def fetch_inventory(self) -> pd.DataFrame:
        """Fetch inventory data."""
        query = "SELECT * FROM inventory"
        return self.execute(query)

    def fetch_sensor_logs(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetch sensor logs."""
        query = "SELECT * FROM sensor_logs"
        return self.execute(query, limit=limit)

    def fetch_robot_sensor_logs(self, robot_id: int, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetch sensor logs for specific robot."""
        query = "SELECT * FROM sensor_logs WHERE robot_id = ?"
        return self.execute(query, params=(robot_id,), limit=limit)
