import re
from pydantic import BaseModel, field_validator
from typing import Optional

ALLOWED_STATES = {"created", "ready", "running", "succeeded", "failed", "deleted"}
SANDBOX_NAME_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")

class RunCreate(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: str
    state: str
    execution_target: str

    @field_validator("execution_target")
    @classmethod
    def validate_execution_target(cls, v: str) -> str:
        if v != "celesto_sandbox":
            raise ValueError(f"execution_target must be exactly 'celesto_sandbox', got '{v}'")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v.lower() not in ALLOWED_STATES:
            raise ValueError(f"state must be one of {ALLOWED_STATES}, got '{v}'")
        return v.lower()

    @field_validator("sandbox_name")
    @classmethod
    def validate_sandbox_name(cls, v: str) -> str:
        if not SANDBOX_NAME_REGEX.match(v):
            raise ValueError(f"sandbox_name must match '^sbx-[a-z0-9]{{8,}}$', got '{v}'")
        return v

class RunResponse(BaseModel):
    run_id: str
    sandbox_name: str
    problem_id: str
    state: str
    execution_target: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
