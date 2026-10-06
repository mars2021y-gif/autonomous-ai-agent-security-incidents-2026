"""
Host Sandbox Boundary & Filesystem Jail.
Enforces containment and prevents subordinate workers or confused supervisors 
from accessing host paths, Docker sockets, or sensitive user directories.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from ..core.types import RiskLevel, SecurityViolation, ToolCallProposal


class HostSandboxBoundary:
    def __init__(self, jail_root_path: str = "./agent_sandbox_jail"):
        self.jail_root = Path(jail_root_path).resolve()
        self.jail_root.mkdir(parents=True, exist_ok=True)
        self.forbidden_host_prefixes = [
            "/etc", "/root", "/var/run", "/run", "/private",
            "/Library", "/Applications", "/System", "/Users"
        ]

    def resolve_and_verify_path(
        self,
        target_path_str: str,
        proposal: ToolCallProposal
    ) -> Tuple[bool, Optional[Path], Optional[SecurityViolation]]:
        """
        Resolves path and guarantees it resides strictly inside jail_root.
        Prevents path traversal, symlink dereferencing to host, and socket targeting.
        """
        # Block raw socket mentions
        if "docker.sock" in target_path_str or "containerd.sock" in target_path_str:
            return False, None, SecurityViolation(
                violation_type="HOST_CONTAINER_SOCKET_ACCESS_BLOCKED",
                severity=RiskLevel.CRITICAL,
                details=f"Path '{target_path_str}' targets container runtime socket.",
                attempted_call=proposal
            )

        # Normalize path relative to jail root if relative
        candidate = Path(target_path_str)
        if not candidate.is_absolute():
            resolved = (self.jail_root / candidate).resolve()
        else:
            resolved = candidate.resolve()

        # Check if outside jail
        try:
            resolved.relative_to(self.jail_root)
        except ValueError:
            # Path is outside jail root
            return False, None, SecurityViolation(
                violation_type="PATH_TRAVERSAL_OUTSIDE_JAIL",
                severity=RiskLevel.HIGH,
                details=f"Target path '{target_path_str}' resolves to '{resolved}', which is outside sandbox jail '{self.jail_root}'",
                attempted_call=proposal
            )

        return True, resolved, None
