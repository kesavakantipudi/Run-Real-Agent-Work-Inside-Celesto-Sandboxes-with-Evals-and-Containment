from fastapi import FastAPI, HTTPException, status
from typing import List
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection, init_db
from app.schemas import RunCreate, RunResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="SandboxShield AI Run Ledger API", version="1.0.0", lifespan=lifespan)

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
    }
}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/runs", response_model=List[RunResponse])
def get_runs():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT run_id, sandbox_name, problem_id, state, execution_target, created_at, updated_at FROM runs ORDER BY id ASC;")
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
    return list(_in_memory_runs.values())

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

    _in_memory_runs[run.run_id] = run_dict
    return run_dict
