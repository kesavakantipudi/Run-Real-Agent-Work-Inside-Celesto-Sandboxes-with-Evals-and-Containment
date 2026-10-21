import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_runs_includes_seed():
    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(r.get("sandbox_name") == "sbx-seeddemo1" for r in data)

def test_post_runs_valid():
    payload = {
        "run_id": "run-test-valid1",
        "sandbox_name": "sbx-testvalid1",
        "problem_id": "prob-test-01",
        "state": "running",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 201
    res = response.json()
    assert res["run_id"] == "run-test-valid1"
    assert res["sandbox_name"] == "sbx-testvalid1"
    assert res["execution_target"] == "celesto_sandbox"

def test_post_runs_invalid_target_rejects():
    payload = {
        "run_id": "run-test-badtarget",
        "sandbox_name": "sbx-testbadtarget",
        "problem_id": "prob-test-01",
        "state": "running",
        "execution_target": "host"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422 or response.status_code == 400

def test_post_runs_invalid_sandbox_name():
    payload = {
        "run_id": "run-test-badname",
        "sandbox_name": "invalid_name",
        "problem_id": "prob-test-01",
        "state": "running",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422 or response.status_code == 400

def test_post_runs_invalid_state():
    payload = {
        "run_id": "run-test-badstate",
        "sandbox_name": "sbx-testbadstate",
        "problem_id": "prob-test-01",
        "state": "unknown_state",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 422 or response.status_code == 400
