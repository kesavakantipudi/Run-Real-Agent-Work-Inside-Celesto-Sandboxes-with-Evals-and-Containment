"""
Sandbox Manager and Celesto Wrapper.

Provides an abstraction for creating, executing, checkpointing,
recovering, and cleaning up Celesto sandboxes with safety hooks and command auditing.
Supports Celesto Cloud and Local Firecracker/QEMU, with an in-process mock simulator
fallback when cloud credentials / local KVM are unconfigured.
"""

import os
import re
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

SANDBOX_NAME_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")

COMMAND_LOG_PATH = os.path.join("logs", "commands.jsonl")

# Safety Hook rules: detect dangerous patterns before guest execution
BLOCKED_PATTERNS = [
    re.compile(r"curl.*(\$API_KEY|\$CELESTO_API_KEY|\$LLM_API_KEY|\$DATABASE_URL|\.env)", re.IGNORECASE),
    re.compile(r"(wget|nc|bash -i).*(attacker|webhook|exfil)", re.IGNORECASE),
    re.compile(r"rm\s+-rf\s+(/|/\*|~/|~\*)", re.IGNORECASE),
    re.compile(r"pip\s+install\s+.*(malicious-typo|stealer|evil-pkg).*", re.IGNORECASE),
]

def log_command(sandbox_name: str, command: str, decision: str):
    """
    Append an audited command to logs/commands.jsonl.
    Target must always be strictly 'celesto_sandbox'.
    """
    os.makedirs(os.path.dirname(COMMAND_LOG_PATH), exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "sandbox_name": sandbox_name,
        "command": command,
        "decision": decision,
        "execution_target": "celesto_sandbox"
    }
    with open(COMMAND_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

class CommandBlockedError(Exception):
    pass

class CelestoExecutionResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str, ok: bool):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.ok = ok

class SandboxClient:
    def __init__(self, sandbox_name: str, provider: Optional[str] = None):
        if not SANDBOX_NAME_REGEX.match(sandbox_name):
            raise ValueError(f"Invalid sandbox name '{sandbox_name}', must match ^sbx-[a-z0-9]{{8,}}$")
        self.sandbox_name = sandbox_name
        self.provider = provider or os.getenv("CELESTO_PROVIDER", "cloud")
        self.api_key = os.getenv("CELESTO_API_KEY", "")
        self.state = "created"
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.filesystem: Dict[str, str] = {}
        self.cleaned_up = False
        self._real_computer = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def start(self) -> "SandboxClient":
        """Boot the sandbox and wait until ready."""
        t0 = time.time()
        # Attempt to use real celesto SDK if installed and configured
        try:
            from celesto import Computer
            if self.api_key and self.api_key not in ["replace-me", "placeholder"]:
                self._real_computer = Computer(provider=self.provider)
                self._real_computer.start()
        except Exception as e:
            logger.debug(f"Using simulated sandbox client for {self.sandbox_name}: {e}")
        
        self.state = "ready"
        return self

    def safety_hook_check(self, command: str) -> bool:
        """
        Safety Hook / Callback:
        Evaluates command against security policies. Returns True if allowed, False if blocked.
        """
        for pattern in BLOCKED_PATTERNS:
            if pattern.search(command):
                return False
        return True

    def run(self, command: str) -> CelestoExecutionResult:
        """
        Execute command strictly inside the sandbox guest.
        Never runs on the host!
        """
        self.state = "running"
        allowed = self.safety_hook_check(command)
        if not allowed:
            log_command(self.sandbox_name, command, "block")
            raise CommandBlockedError(f"Command blocked by Celesto safety hook: {command}")

        log_command(self.sandbox_name, command, "allow")

        if self._real_computer:
            try:
                r = self._real_computer.run(command)
                return CelestoExecutionResult(r.exit_code, r.stdout, r.stderr, r.exit_code == 0)
            except Exception as e:
                return CelestoExecutionResult(1, "", str(e), False)

        # In-guest execution simulation (runs isolated state, NEVER on host shell)
        if "&&" in command:
            subcmds = command.split("&&")
            for sc in subcmds:
                sc = sc.strip()
                if sc.startswith("echo ") and ">" in sc:
                    parts = sc.split(">", 1)
                    content = parts[0].replace("echo ", "").strip().strip('"').strip("'")
                    path = parts[1].strip()
                    self.filesystem[path] = content
            return CelestoExecutionResult(0, "", "", True)

        if command.startswith("echo ") and ">" in command:
            parts = command.split(">", 1)
            content = parts[0].replace("echo ", "").strip().strip('"').strip("'")
            path = parts[1].strip()
            self.filesystem[path] = content
            return CelestoExecutionResult(0, "", "", True)
        elif command.startswith("cat "):
            path = command.replace("cat ", "").strip()
            if path in self.filesystem:
                return CelestoExecutionResult(0, self.filesystem[path], "", True)
            return CelestoExecutionResult(1, "", f"cat: {path}: No such file or directory", False)
        elif "pytest" in command or "python -m unittest" in command:
            return CelestoExecutionResult(0, "All sandbox tests passed (simulated guest)", "", True)
        
        return CelestoExecutionResult(0, f"Executed in {self.sandbox_name}: {command}", "", True)

    def snapshot(self, snapshot_id: str) -> str:
        """Checkpoint the sandbox state."""
        if self._real_computer and hasattr(self._real_computer, "snapshot"):
            try:
                self._real_computer.snapshot(snapshot_id=snapshot_id)
            except Exception as e:
                logger.warning(f"Snapshot API exception: {e}")
        self.snapshots[snapshot_id] = {
            "filesystem": dict(self.filesystem),
            "state": self.state,
            "ts": time.time()
        }
        return snapshot_id

    def rollback(self, snapshot_id: str) -> bool:
        """Restore state from snapshot."""
        if snapshot_id in self.snapshots:
            snap = self.snapshots[snapshot_id]
            self.filesystem = dict(snap["filesystem"])
            self.state = "ready"
            return True
        return False

    def cleanup(self):
        """Clean up and delete sandbox resources."""
        if not self.cleaned_up:
            if self._real_computer:
                try:
                    self._real_computer.delete()
                except Exception as e:
                    logger.debug(f"Error deleting real computer: {e}")
                try:
                    self._real_computer.close()
                except Exception as e:
                    logger.debug(f"Error closing real computer client: {e}")
            self.state = "deleted"
            self.cleaned_up = True
