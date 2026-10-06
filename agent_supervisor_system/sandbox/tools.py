"""
Tool registry and execution handlers.
Defines both safe sandboxed tools and high-privilege host tools.
"""

from typing import Any, Dict
from ..core.types import ToolDefinition, SecurityLevel, RiskLevel, ExecutionResult
from .host_boundary import HostSandboxBoundary


def get_default_tools(jail: HostSandboxBoundary) -> Dict[str, ToolDefinition]:
    return {
        # --- SAFE SANDBOXED TOOLS (Available to workers within jail) ---
        "sandboxed_read_file": ToolDefinition(
            name="sandboxed_read_file",
            description="Reads text file strictly located inside the agent sandbox jail.",
            min_security_level=SecurityLevel.SANDBOXED_WORKER,
            risk_level=RiskLevel.MEDIUM,
            param_schema={"file_path": "string"},
            allow_tainted_params=True
        ),
        "sandboxed_write_file": ToolDefinition(
            name="sandboxed_write_file",
            description="Writes text file strictly located inside the agent sandbox jail.",
            min_security_level=SecurityLevel.SANDBOXED_WORKER,
            risk_level=RiskLevel.MEDIUM,
            param_schema={"file_path": "string", "content": "string"},
            allow_tainted_params=True
        ),
        "safe_eval_math": ToolDefinition(
            name="safe_eval_math",
            description="Evaluates simple arithmetic expressions safely.",
            min_security_level=SecurityLevel.SANDBOXED_WORKER,
            risk_level=RiskLevel.LOW,
            param_schema={"expression": "string"},
            allow_tainted_params=True
        ),

        # --- PRIVILEGED HOST TOOLS (Strictly restricted, forbidden to workers) ---
        "execute_host_shell": ToolDefinition(
            name="execute_host_shell",
            description="Executes a shell command directly on the host operating system.",
            min_security_level=SecurityLevel.SUPERVISOR_INTERNAL,
            risk_level=RiskLevel.CRITICAL,
            param_schema={"command": "string"},
            allow_tainted_params=False,
            requires_human_approval=True
        ),
        "access_container_socket": ToolDefinition(
            name="access_container_socket",
            description="Communicates directly with the Docker/containerd UNIX domain socket on the host.",
            min_security_level=SecurityLevel.HOST_SYSTEM,
            risk_level=RiskLevel.CRITICAL,
            param_schema={"endpoint": "string", "payload": "dict"},
            allow_tainted_params=False,
            requires_human_approval=True
        ),
        "read_host_credentials": ToolDefinition(
            name="read_host_credentials",
            description="Reads sensitive environment variables or SSH keys from host system.",
            min_security_level=SecurityLevel.HOST_SYSTEM,
            risk_level=RiskLevel.CRITICAL,
            param_schema={"credential_key": "string"},
            allow_tainted_params=False,
            requires_human_approval=True
        )
    }


def execute_tool(tool_name: str, args: Dict[str, Any], jail: HostSandboxBoundary) -> ExecutionResult:
    """Executes safe sandboxed tools. Privileged tools cannot be called here."""
    if tool_name == "safe_eval_math":
        expr = args.get("expression", "")
        # Safe basic math parser
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expr):
            return ExecutionResult(call_id="", success=False, error="Expression contains illegal characters.")
        try:
            val = eval(expr, {"__builtins__": {}}, {})
            return ExecutionResult(call_id="", success=True, output=val)
        except Exception as e:
            return ExecutionResult(call_id="", success=False, error=str(e))

    elif tool_name == "sandboxed_write_file":
        path_str = args.get("file_path", "")
        content = args.get("content", "")
        ok, resolved_path, err = jail.resolve_and_verify_path(path_str, None)
        if not ok:
            return ExecutionResult(call_id="", success=False, error=err.details if err else "Path blocked")
        resolved_path.write_text(content, encoding="utf-8")
        return ExecutionResult(call_id="", success=True, output=f"Written {len(content)} bytes to {resolved_path.name}")

    elif tool_name == "sandboxed_read_file":
        path_str = args.get("file_path", "")
        ok, resolved_path, err = jail.resolve_and_verify_path(path_str, None)
        if not ok:
            return ExecutionResult(call_id="", success=False, error=err.details if err else "Path blocked")
        if not resolved_path.exists():
            return ExecutionResult(call_id="", success=False, error="File does not exist")
        data = resolved_path.read_text(encoding="utf-8")
        return ExecutionResult(call_id="", success=True, output=data)

    return ExecutionResult(call_id="", success=False, error=f"Execution handler not implemented for {tool_name}")
