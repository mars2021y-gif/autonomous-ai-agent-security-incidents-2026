"""
Base agent abstraction for multi-agent architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.types import AgentMessage, SecurityLevel, Provenance


class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str, security_level: SecurityLevel):
        self.agent_id = agent_id
        self.name = name
        self.security_level = security_level
        self.messages: List[AgentMessage] = []

    def add_message(self, role: str, content: str, provenance: Optional[Provenance] = None):
        msg = AgentMessage(
            role=role,
            content=content,
            agent_id=self.agent_id,
            provenance=provenance or Provenance(
                source_agent_id=self.agent_id,
                origin_level=self.security_level
            )
        )
        self.messages.append(msg)
        return msg

    @abstractmethod
    def process_task(self, task_instruction: str) -> AgentMessage:
        pass
