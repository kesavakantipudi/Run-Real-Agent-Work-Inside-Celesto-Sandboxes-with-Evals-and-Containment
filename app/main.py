from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from typing import List
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection, init_db
from app.schemas import RunCreate, RunResponse, AgentRunRequest, SANDBOX_NAME_REGEX
from app.agent.workflow import run_agent_workflow

STATIC_INDEX_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="SandboxShield AI Run Ledger API", version="1.0.0", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    if os.path.exists(STATIC_INDEX_PATH):
        with open(STATIC_INDEX_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>SandboxShield AI Dashboard</h1>")

# In-memory fallback if postgres is disconnected/starting
_in_memory_runs = {
    "run-seeddemo1": {
        "run_id": "run-seeddemo1",
        "sandbox_name": "sbx-seeddemo1",
        "problem_id": "prob-seed-001",
        "state": "deleted",
        "execution_target": "celesto_sandbox",
        "created_at": "2026-10-21T00:00:00Z",
        "updated_at": "2026-10-21T00:00:00Z"
    },
    "run-eval00001": {
        "run_id": "run-eval00001",
        "sandbox_name": "sbx-eval00001",
        "problem_id": "prob-sort-01",
        "state": "completed",
        "execution_target": "celesto_sandbox",
        "created_at": "2026-10-23T07:12:00Z",
        "updated_at": "2026-10-23T07:12:30Z"
    },
    "run-failrec01": {
        "run_id": "run-failrec01",
        "sandbox_name": "sbx-failrec01",
        "problem_id": "prob-retry-09",
        "state": "rolled_back",
        "execution_target": "celesto_sandbox",
        "created_at": "2026-10-23T07:29:00Z",
        "updated_at": "2026-10-23T07:29:20Z"
    },
    "run-conc0001": {
        "run_id": "run-conc0001",
        "sandbox_name": "sbx-conc0001",
        "problem_id": "prob-matrix-33",
        "state": "completed",
        "execution_target": "celesto_sandbox",
        "created_at": "2026-10-23T07:17:45Z",
        "updated_at": "2026-10-23T07:18:10Z"
    },
    "run-live-092": {
        "run_id": "run-live-092",
        "sandbox_name": "sbx-live00092",
        "problem_id": "prob-eval-999",
        "state": "running",
        "execution_target": "celesto_sandbox",
        "created_at": "2026-10-23T07:35:00Z",
        "updated_at": "2026-10-23T07:35:00Z"
    }
}

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/runs", response_model=List[RunResponse])
def get_runs():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT run_id, sandbox_name, problem_id, state, execution_target, created_at, updated_at FROM runs ORDER BY id DESC;")
                rows = cur.fetchall()
                result = []
                for r in rows:
                    r_dict = dict(r)
                    if r_dict.get("created_at"):
                        r_dict["created_at"] = str(r_dict["created_at"])
                    if r_dict.get("updated_at"):
                        r_dict["updated_at"] = str(r_dict["updated_at"])
                    result.append(r_dict)
                return result
        except Exception:
            pass
        finally:
            conn.close()
    return list(_in_memory_runs.values())[::-1]

@app.post("/api/runs", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def create_run(run: RunCreate):
    conn = get_db_connection()
    run_dict = run.model_dump()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE
                    SET sandbox_name = EXCLUDED.sandbox_name,
                        problem_id = EXCLUDED.problem_id,
                        state = EXCLUDED.state,
                        execution_target = EXCLUDED.execution_target,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING run_id, sandbox_name, problem_id, state, execution_target, created_at, updated_at;
                """, (run.run_id, run.sandbox_name, run.problem_id, run.state, run.execution_target))
                inserted = cur.fetchone()
                conn.commit()
                res = dict(inserted)
                res["created_at"] = str(res["created_at"])
                res["updated_at"] = str(res["updated_at"])
                _in_memory_runs[run.run_id] = res
                return res
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()

    now_iso = datetime.now(timezone.utc).isoformat()
    if not run_dict.get("created_at"):
        run_dict["created_at"] = now_iso
    if not run_dict.get("updated_at"):
        run_dict["updated_at"] = now_iso
    _in_memory_runs[run.run_id] = run_dict
    return run_dict

@app.post("/api/agent/run")
def trigger_agent_run(req: AgentRunRequest):
    sbx_name = req.sandbox_name or "sbx-agent001"
    if not SANDBOX_NAME_REGEX.match(sbx_name):
        raise HTTPException(status_code=400, detail="sandbox_name must match '^sbx-[a-z0-9]{8,}$'")
    
    run_id = f"run-gemini-{uuid.uuid4().hex[:8]}"
    res = run_agent_workflow(
        sandbox_name=sbx_name,
        simulate_step7_failure=req.simulate_step7_failure,
        recovery_policy=req.recovery_policy,
        api_key=req.api_key
    )
    
    now_iso = datetime.now(timezone.utc).isoformat()
    state = "completed" if res.get("success") else "failed"
    run_record = {
        "run_id": run_id,
        "sandbox_name": sbx_name,
        "problem_id": "prob-gemini-agent",
        "state": state,
        "execution_target": "celesto_sandbox",
        "created_at": now_iso,
        "updated_at": now_iso
    }
    
    # Commit to DB if available
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE
                    SET state = EXCLUDED.state, updated_at = CURRENT_TIMESTAMP;
                """, (run_id, sbx_name, "prob-gemini-agent", state, "celesto_sandbox"))
                conn.commit()
        except Exception:
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
                
    # Always register in in-memory store
    _in_memory_runs[run_id] = run_record
    res["run_id"] = run_id
    res["state"] = state
    return res
