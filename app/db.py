import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ledger:ledger@localhost:5432/ledger")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        logger.warning("Could not connect to database to initialize schema; assuming migrations/seeds handle it or DB is remote.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
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
            """)
            # Ensure seed row exists if table was newly created
            cur.execute("""
                INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target)
                VALUES ('run-seeddemo1', 'sbx-seeddemo1', 'prob-seed-001', 'deleted', 'celesto_sandbox')
                ON CONFLICT (run_id) DO NOTHING;
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Error in init_db: {e}")
        conn.rollback()
    finally:
        conn.close()
