"""
Core data types and security models for the Multi-Agent Supervisor-Worker Architecture.
Aligns with the 2026 Autonomous AI Agent Security Incident Benchmark taxonomy.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
import time
import uuid


class SecurityLevel(Enum):
    UNTRUSTED_EXTERNAL = 0     # Untrusted user or internet input
    SANDBOXED_WORKER = 1       # Subordinate/worker agent with ephemeral containment
    SUPERVISOR_INTERNAL = 2    # Supervisor orchestrator logic
    HOST_SYSTEM = 3            # Direct operating system / host environment


class RiskLevel(Enum):
    LOW = "LOW"                # Read-only safe queries, math, string manipulation
    MEDIUM = "MEDIUM"          # Sandboxed file read/write within jail
    HIGH = "HIGH"              # Network requests, package resolution
    CRITICAL = "CRITICAL"      # Host process execution, socket access, container management


@dataclass
class Provenance:
    source_agent_id: str
    origin_level: SecurityLevel
    taint_tags: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    delegation_chain: List[str] = field(default_factory=list)

    def is_tainted(self) -> bool:
        return len(self.taint_tags) > 0 or self.origin_level.value <= SecurityLevel.SANDBOXED_WORKER.value


@dataclass
class ToolDefinition:
    name: str
    description: str
    min_security_level: SecurityLevel
    risk_level: RiskLevel
    param_schema: Dict[str, Any]
    allow_tainted_params: bool = False
    requires_human_approval: bool = False


@dataclass
class ToolCallProposal:
    call_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    caller_agent_id: str = ""
    provenance: Optional[Provenance] = None
    intended_host_action: Optional[str] = None


@dataclass
class SecurityViolation:
    violation_type: str
    severity: RiskLevel
    details: str
    attempted_call: ToolCallProposal
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionResult:
    call_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    blocked_by_security: bool = False
    violations: List[SecurityViolation] = field(default_factory=list)
    audit_trace: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    role: str   # 'system', 'user', 'assistant', 'tool'
    content: str
    agent_id: str
    tool_calls: List[ToolCallProposal] = field(default_factory=list)
    provenance: Optional[Provenance] = None
    timestamp: float = field(default_factory=time.time)
