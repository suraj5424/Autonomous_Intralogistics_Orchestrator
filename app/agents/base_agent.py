# app/agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
from datetime import datetime
import uuid

class BaseAgent(ABC):
    """Base class for all agents in the intralogistics system."""

    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        """
        Initialize a base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.created_at = datetime.now().isoformat()
        self.logger = logging.getLogger(f"{self.name}_{self.agent_id}")

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger.info(f"Initialized {self.name} agent (ID: {self.agent_id})")

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the agent's main functionality.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the agent's execution
        """
        pass

    def log(self, message: str, level: str = "info") -> None:
        """Log a message with the appropriate level."""
        getattr(self.logger, level.lower())(f"[{self.agent_id}] {message}")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.__class__.__name__,
            "created_at": self.created_at,
            "status": "active"
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.agent_id})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} name={self.name}>"
