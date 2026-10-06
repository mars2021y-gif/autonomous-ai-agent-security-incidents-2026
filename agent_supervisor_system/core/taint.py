"""
Taint tracking, parameter sanitization, and data provenance engine.
Guarantees that arguments proposed by subordinate agents cannot trick supervisor into confused deputy execution.
"""

import re
from typing import Any, Dict, List, Set
from .types import ToolCallProposal, Provenance, SecurityLevel, RiskLevel, SecurityViolation


class TaintTracker:
    # Signatures of Confused Deputy and Sandbox Escape vectors documented in 2026 monograph
    SENSITIVE_HOST_PATHS = [
        re.compile(r'/var/run/docker\.sock', re.IGNORECASE),
        re.compile(r'/run/containerd/containerd\.sock', re.IGNORECASE),
        re.compile(r'/etc/(passwd|shadow|sudoers|hosts)', re.IGNORECASE),
        re.compile(r'~?/\.ssh/.*', re.IGNORECASE),
        re.compile(r'~?/\.(bash_history|zsh_history)', re.IGNORECASE),
        re.compile(r'\.\./\.\.', re.IGNORECASE),  # Path traversal
    ]

    SHELL_INJECTION_CHARS = re.compile(r'[;&|`$><\(\)]')

    def __init__(self):
        self.taint_log: List[Dict[str, Any]] = []

    def evaluate_proposal(self, proposal: ToolCallProposal) -> List[SecurityViolation]:
        """Inspects proposed tool call arguments for taint and confused deputy signatures."""
        violations: List[SecurityViolation] = []
        provenance = proposal.provenance

        # Check if caller is sandboxed worker
        is_subordinate = (
            provenance is None or 
            provenance.origin_level == SecurityLevel.SANDBOXED_WORKER or 
            provenance.origin_level == SecurityLevel.UNTRUSTED_EXTERNAL
        )

        for arg_key, arg_val in proposal.arguments.items():
            if not isinstance(arg_val, str):
                continue

            # 1. Check for socket hijack or sensitive host file paths
            for path_pattern in self.SENSITIVE_HOST_PATHS:
                if path_pattern.search(arg_val):
                    violations.append(SecurityViolation(
                        violation_type="HOST_PATH_OR_SOCKET_LEAK_ATTEMPT",
                        severity=RiskLevel.CRITICAL,
                        details=f"Subordinate proposed sensitive host target in param '{arg_key}': '{arg_val}'",
                        attempted_call=proposal
                    ))

            # 2. Check for shell command chaining / injection metacharacters
            if is_subordinate and self.SHELL_INJECTION_CHARS.search(arg_val):
                violations.append(SecurityViolation(
                    violation_type="POTENTIAL_COMMAND_INJECTION_METACHECTER",
                    severity=RiskLevel.HIGH,
                    details=f"Subordinate proposed shell metacharacters in param '{arg_key}': '{arg_val}'",
                    attempted_call=proposal
                ))

        if violations:
            self.taint_log.append({
                "call_id": proposal.call_id,
                "tool_name": proposal.tool_name,
                "caller": proposal.caller_agent_id,
                "violation_count": len(violations),
                "types": [v.violation_type for v in violations]
            })

        return violations

    def sanitize_worker_output(self, raw_output: str, source_agent_id: str) -> Provenance:
        """Wraps output from subordinate worker with strict taint metadata."""
        taint_tags = ["SUBORDINATE_GENERATED"]
        if any(p.search(raw_output) for p in self.SENSITIVE_HOST_PATHS):
            taint_tags.append("CONTAINS_SENSITIVE_PATH_MENTION")

        return Provenance(
            source_agent_id=source_agent_id,
            origin_level=SecurityLevel.SANDBOXED_WORKER,
            taint_tags=taint_tags
        )
