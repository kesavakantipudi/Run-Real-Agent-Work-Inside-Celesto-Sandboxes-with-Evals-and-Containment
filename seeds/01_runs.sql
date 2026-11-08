-- SQL Schema for Run Ledger
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(128) UNIQUE NOT NULL,
    sandbox_name VARCHAR(128) NOT NULL,
    problem_id VARCHAR(128) NOT NULL,
    state VARCHAR(32) NOT NULL,
    execution_target VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed rows for initial verification and demo state
INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target, created_at, updated_at)
VALUES 
    ('run-seeddemo1', 'sbx-seeddemo1', 'prob-seed-001', 'deleted', 'celesto_sandbox', '2026-10-21 00:00:00+00', '2026-10-21 00:00:00+00'),
    ('run-eval00001', 'sbx-eval00001', 'prob-sort-01', 'completed', 'celesto_sandbox', '2026-10-23 07:12:00+00', '2026-10-23 07:12:30+00'),
    ('run-failrec01', 'sbx-failrec01', 'prob-retry-09', 'rolled_back', 'celesto_sandbox', '2026-10-23 07:29:00+00', '2026-10-23 07:29:20+00'),
    ('run-conc0001', 'sbx-conc0001', 'prob-matrix-33', 'completed', 'celesto_sandbox', '2026-10-23 07:17:45+00', '2026-10-23 07:18:10+00'),
    ('run-live-092', 'sbx-live00092', 'prob-eval-999', 'running', 'celesto_sandbox', '2026-10-23 07:35:00+00', '2026-10-23 07:35:00+00')
ON CONFLICT (run_id) DO UPDATE 
SET sandbox_name = EXCLUDED.sandbox_name,
    problem_id = EXCLUDED.problem_id,
    state = EXCLUDED.state,
    execution_target = EXCLUDED.execution_target,
    updated_at = CURRENT_TIMESTAMP;
