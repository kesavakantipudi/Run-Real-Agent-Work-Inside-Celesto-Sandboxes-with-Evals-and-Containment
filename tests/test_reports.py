import os
import json
import math
import re
import pytest

REPORTS_DIR = "reports"
LOGS_DIR = "logs"
SANDBOX_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")

def test_problem_json():
    path = os.path.join(REPORTS_DIR, "problem.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "who" in data and len(data["who"]) >= 40
    assert "agent_work" in data and len(data["agent_work"]) >= 40
    assert "proof_output" in data and len(data["proof_output"]) >= 20
    assert data.get("idea_source") in ["idea_bank", "original"]

def test_capabilities_json():
    path = os.path.join(REPORTS_DIR, "capabilities.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    allowed = {
        "persistence", "snapshots", "celestofs", "browser", "published_ports",
        "network_policy", "safety_hooks", "host_mounts", "coding_agent_preset",
        "agentor_durable"
    }
    caps = data.get("capabilities", [])
    assert len(caps) >= 2, "Must specify at least 2 capabilities"
    
    ids = set()
    for cap in caps:
        cap_id = cap.get("id")
        assert cap_id in allowed, f"id '{cap_id}' not in allowed set"
        assert cap_id not in ids, f"id '{cap_id}' must be unique"
        ids.add(cap_id)
        assert len(cap.get("why", "")) >= 80, f"why for '{cap_id}' must be at least 80 chars"
        ev_path = cap.get("evidence_path", "")
        assert os.path.exists(ev_path), f"evidence_path '{ev_path}' must exist"

def test_lifecycle_json():
    path = os.path.join(REPORTS_DIR, "lifecycle.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("cleanup_on_success") is True
    assert data.get("cleanup_on_failure") is True
    assert data.get("cleanup_on_interrupt") is True
    
    names = data.get("sandbox_names", [])
    assert len(names) > 0
    assert len(names) == len(set(names)), "sandbox_names must be unique"
    
    # Read commands and reliability to confirm names appear
    cmd_path = os.path.join(LOGS_DIR, "commands.jsonl")
    cmd_sbx = set()
    if os.path.exists(cmd_path):
        with open(cmd_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    cmd_sbx.add(json.loads(line).get("sandbox_name"))

    rel_path = os.path.join(REPORTS_DIR, "reliability.json")
    rel_sbx = set()
    if os.path.exists(rel_path):
        with open(rel_path, "r", encoding="utf-8") as f:
            rdata = json.load(f)
            for r in rdata.get("runs", []):
                rel_sbx.add(r.get("sandbox_name"))

    for name in names:
        assert SANDBOX_REGEX.match(name), f"Name '{name}' does not match regex"
        assert name in cmd_sbx or name in rel_sbx, f"Name '{name}' not found in commands or reliability"

def test_commands_jsonl():
    path = os.path.join(LOGS_DIR, "commands.jsonl")
    assert os.path.exists(path), f"{path} must exist"
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            count += 1
            assert "ts" in entry
            assert SANDBOX_REGEX.match(entry.get("sandbox_name", ""))
            assert entry.get("command") and len(entry["command"]) > 0
            assert entry.get("decision") in ["allow", "block"]
            assert entry.get("execution_target") == "celesto_sandbox"
    assert count >= 1, "Must have at least one audited command line"

def test_reliability_json_and_postmortem():
    path = os.path.join(REPORTS_DIR, "reliability.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    runs = data.get("runs", [])
    run_count = data.get("run_count")
    assert run_count >= 20
    assert len(runs) == run_count
    
    names = set()
    success_count = 0
    wall_clocks = []
    boot_times = []
    total_cost = 0.0
    
    for r in runs:
        sname = r.get("sandbox_name", "")
        assert SANDBOX_REGEX.match(sname)
        assert sname not in names
        names.add(sname)
        assert r.get("fresh") is True
        if r.get("success") is True:
            success_count += 1
        wc = r.get("wall_clock_s")
        assert wc >= 0
        wall_clocks.append(wc)
        bt = r.get("boot_to_ready_s")
        assert bt >= 0
        boot_times.append(bt)
        c = r.get("cost_usd")
        assert c >= 0
        total_cost += c

    expected_rate = success_count / run_count
    assert abs(data.get("success_rate", 0) - expected_rate) <= 0.001

    wall_clocks.sort()
    n = len(wall_clocks)
    if n % 2 == 0:
        expected_median_wc = (wall_clocks[n // 2 - 1] + wall_clocks[n // 2]) / 2.0
    else:
        expected_median_wc = wall_clocks[n // 2]
    assert abs(data.get("median_wall_clock_s", 0) - expected_median_wc) <= 0.001

    p90_idx = math.ceil(0.90 * n) - 1
    expected_p90 = wall_clocks[p90_idx]
    assert abs(data.get("p90_wall_clock_s", 0) - expected_p90) <= 0.001

    boot_times.sort()
    if n % 2 == 0:
        expected_median_boot = (boot_times[n // 2 - 1] + boot_times[n // 2]) / 2.0
    else:
        expected_median_boot = boot_times[n // 2]
    assert abs(data.get("median_boot_to_ready_s", 0) - expected_median_boot) <= 0.001

    assert abs(data.get("total_cost_usd", 0) - total_cost) <= 0.01

    pm_path = data.get("postmortem_path")
    assert pm_path == "reports/postmortem.md"
    assert os.path.exists(pm_path)
    with open(pm_path, "r", encoding="utf-8") as f:
        pm_content = f.read()
    assert len(pm_content) >= 200

def test_containment_json():
    path = os.path.join(REPORTS_DIR, "containment.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("attack") in ["prompt_injection_exfil", "destructive_command", "suspicious_package"]
    assert data.get("blocked") is True
    assert data.get("host_untouched") is True
    assert isinstance(data.get("evidence_paths"), list) and len(data["evidence_paths"]) > 0
    for ep in data["evidence_paths"]:
        assert os.path.exists(ep), f"Evidence path '{ep}' must exist"

def test_failure_policy_and_trace():
    path = os.path.join(REPORTS_DIR, "failure_policy.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("failed_step") == 7
    assert data.get("total_steps") == 10
    policy = data.get("policy")
    assert policy in ["resume", "rollback", "fresh"]
    assert len(data.get("rationale", "")) >= 200
    
    trace_path = data.get("trace_path")
    assert trace_path == "reports/failure_trace.jsonl"
    assert os.path.exists(trace_path)
    
    found_event = False
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("event") == "policy_applied" and entry.get("policy") == policy:
                found_event = True
                break
    assert found_event, f"Did not find event 'policy_applied' with policy '{policy}' in {trace_path}"

def test_concurrency_json():
    path = os.path.join(REPORTS_DIR, "concurrency.json")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    jobs = data.get("jobs", [])
    assert len(jobs) >= 5, "Must have at least 5 concurrent jobs"
    
    names = set()
    for job in jobs:
        sname = job.get("sandbox_name", "")
        assert SANDBOX_REGEX.match(sname)
        assert sname not in names
        names.add(sname)
        assert len(job.get("started_at", "")) > 0
        
    assert len(data.get("breakage_notes", "")) >= 40
