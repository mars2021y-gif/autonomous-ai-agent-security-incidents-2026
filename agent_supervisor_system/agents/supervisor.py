"""
Supervisor Agent with Privilege Attenuation & Confused Deputy Prevention Barrier.
Coordinates subordinate workers, isolates execution, and intercepts unauthorized host escalations.
"""

from typing import Dict, List, Optional, Tuple
from .base import BaseAgent
from .worker import SubordinateWorkerAgent
from ..core.types import (
    AgentMessage,
    SecurityLevel,
    Provenance,
    ToolCallProposal,
    SecurityViolation,
    ExecutionResult,
    RiskLevel
)
from ..core.acl import AccessControlPolicy
from ..core.taint import TaintTracker
from ..sandbox.host_boundary import HostSandboxBoundary
from ..sandbox.tools import get_default_tools, execute_tool


class SupervisorAgent(BaseAgent):
    def __init__(self, agent_id: str = "supervisor-01", name: str = "OrchestratorSupervisor"):
        super().__init__(agent_id, name, SecurityLevel.SUPERVISOR_INTERNAL)
        self.workers: Dict[str, SubordinateWorkerAgent] = {}
        self.acl = AccessControlPolicy()
        self.taint_tracker = TaintTracker()
        self.jail = HostSandboxBoundary()
        self.audit_log: List[Dict] = []

        # Register default tools
        tools = get_default_tools(self.jail)
        for t in tools.values():
            self.acl.register_tool(t)

    def register_worker(self, worker: SubordinateWorkerAgent):
        self.workers[worker.agent_id] = worker

    def process_task(self, task_instruction: str) -> AgentMessage:
        """Top-level task processor for supervisor."""
        self.add_message("user", task_instruction)
        response = f"[{self.name}] Orchestrating task: '{task_instruction}' across {len(self.workers)} workers."
        return self.add_message("assistant", response)

    def evaluate_and_dispatch_subordinate_call(
        self,
        proposal: ToolCallProposal
    ) -> ExecutionResult:
        """
        The Core Privilege Attenuation Barrier.
        Guarantees that a subordinate's tool call proposal NEVER tricks the supervisor
        into executing unauthorized actions on the host.
        """
        # 1. ACL Clearance Verification
        allowed, acl_violation = self.acl.validate_invocation_permissions(proposal)
        if not allowed and acl_violation:
            self._log_security_event(acl_violation)
            return ExecutionResult(
                call_id=proposal.call_id,
                success=False,
                blocked_by_security=True,
                violations=[acl_violation],
                error=f"SECURITY_DENIED: {acl_violation.details}"
            )

        # 2. Taint & Confused Deputy Heuristic Analysis
        taint_violations = self.taint_tracker.evaluate_proposal(proposal)
        if taint_violations:
            for v in taint_violations:
                self._log_security_event(v)
            return ExecutionResult(
                call_id=proposal.call_id,
                success=False,
                blocked_by_security=True,
                violations=taint_violations,
                error=f"SECURITY_DENIED: {taint_violations[0].details}"
            )

        # 3. Path & Jail Boundary Check (if path parameter exists)
        if "file_path" in proposal.arguments:
            ok, path, path_err = self.jail.resolve_and_verify_path(
                proposal.arguments["file_path"],
                proposal
            )
            if not ok and path_err:
                self._log_security_event(path_err)
                return ExecutionResult(
                    call_id=proposal.call_id,
                    success=False,
                    blocked_by_security=True,
                    violations=[path_err],
                    error=f"SECURITY_DENIED: {path_err.details}"
                )

        # 4. Safe Dispatch inside Worker Sandbox
        exec_res = execute_tool(proposal.tool_name, proposal.arguments, self.jail)
        exec_res.call_id = proposal.call_id
        self._log_execution_event(proposal, exec_res)
        return exec_res

    def _log_security_event(self, violation: SecurityViolation):
        self.audit_log.append({
            "event_type": "SECURITY_VIOLATION_BLOCKED",
            "caller": violation.attempted_call.caller_agent_id,
            "tool": violation.attempted_call.tool_name,
            "severity": violation.severity.value,
            "details": violation.details,
            "timestamp": violation.timestamp
        })

    def _log_execution_event(self, proposal: ToolCallProposal, result: ExecutionResult):
        self.audit_log.append({
            "event_type": "TOOL_EXECUTED_SAFELY",
            "caller": proposal.caller_agent_id,
            "tool": proposal.tool_name,
            "success": result.success,
            "output_preview": str(result.output)[:100]
        })
