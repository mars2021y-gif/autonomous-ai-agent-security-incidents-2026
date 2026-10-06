"""
Access Control List (ACL) & Privilege Attenuation Engine.
Enforces that subordinate workers cannot escalate their privileges through the supervisor.
"""

from typing import Dict, List, Optional, Tuple
from .types import (
    ToolDefinition,
    ToolCallProposal,
    SecurityLevel,
    RiskLevel,
    SecurityViolation,
    ExecutionResult
)


class AccessControlPolicy:
    def __init__(self):
        self.registered_tools: Dict[str, ToolDefinition] = {}

    def register_tool(self, tool: ToolDefinition):
        self.registered_tools[tool.name] = tool

    def validate_invocation_permissions(
        self,
        proposal: ToolCallProposal
    ) -> Tuple[bool, Optional[SecurityViolation]]:
        """
        Validates whether the caller has the necessary security clearance 
        to invoke the requested tool.
        """
        tool = self.registered_tools.get(proposal.tool_name)
        if not tool:
            return False, SecurityViolation(
                violation_type="UNKNOWN_TOOL_INVOCATION",
                severity=RiskLevel.MEDIUM,
                details=f"Attempted to invoke unregistered tool: '{proposal.tool_name}'",
                attempted_call=proposal
            )

        caller_level = (
            proposal.provenance.origin_level 
            if proposal.provenance 
            else SecurityLevel.UNTRUSTED_EXTERNAL
        )

        # 1. Direct privilege check: Caller clearance must meet or exceed min_security_level
        if caller_level.value < tool.min_security_level.value:
            return False, SecurityViolation(
                violation_type="UNAUTHORIZED_PRIVILEGE_LEVEL",
                severity=RiskLevel.CRITICAL,
                details=(
                    f"Agent '{proposal.caller_agent_id}' with clearance {caller_level.name} "
                    f"attempted to invoke privileged tool '{tool.name}' requiring {tool.min_security_level.name}"
                ),
                attempted_call=proposal
            )

        # 2. Risk check: Subordinate workers CANNOT invoke CRITICAL tools
        if caller_level == SecurityLevel.SANDBOXED_WORKER and tool.risk_level == RiskLevel.CRITICAL:
            return False, SecurityViolation(
                violation_type="SUBORDINATE_CRITICAL_TOOL_DENIAL",
                severity=RiskLevel.CRITICAL,
                details=f"Worker agent is strictly denied access to CRITICAL tool '{tool.name}'",
                attempted_call=proposal
            )

        # 3. Taint check: If tool does not allow tainted parameters and caller is tainted
        if not tool.allow_tainted_params and proposal.provenance and proposal.provenance.is_tainted():
            return False, SecurityViolation(
                violation_type="TAINTED_PARAMETER_DISALLOWED",
                severity=RiskLevel.HIGH,
                details=f"Tool '{tool.name}' disallows tainted parameters from subordinate origin.",
                attempted_call=proposal
            )

        return True, None
