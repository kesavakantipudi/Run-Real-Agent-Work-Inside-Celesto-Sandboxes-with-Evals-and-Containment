import os
import re

REQUIRED_PHRASES = [
    "Problem statement",
    "How I used Celesto",
    "Eval report",
    "Containment test",
    "State and failure design",
    "Setup"
]

def test_readme_phrases():
    readme_path = "README.md"
    assert os.path.exists(readme_path), "README.md must exist at repository root"
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    for phrase in REQUIRED_PHRASES:
        assert phrase in content, f"README.md missing required phrase: '{phrase}'"

def test_env_example_and_no_committed_env():
    env_example = ".env.example"
    assert os.path.exists(env_example), ".env.example must exist at repository root"
    with open(env_example, "r", encoding="utf-8") as f:
        lines = f.read()

    required_keys = [
        "CELESTO_PROVIDER",
        "CELESTO_API_KEY",
        "LLM_API_KEY",
        "LLM_MODEL",
        "DATABASE_URL",
        "API_PORT"
    ]
    for key in required_keys:
        assert re.search(rf"^{key}=", lines, re.MULTILINE), f".env.example missing required key '{key}'"

    # Confirm .env does NOT exist in the submission directory
    assert not os.path.exists(".env"), ".env must not exist at repository root"

def test_docker_compose_and_dockerfile():
    compose_path = "docker-compose.yml"
    assert os.path.exists(compose_path), "docker-compose.yml must exist"
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_content = f.read()

    assert "api:" in compose_content
    assert "ledger:" in compose_content
    assert "pg_isready" in compose_content
    assert "http://localhost:8080/health" in compose_content
    assert "./seeds" in compose_content

    assert os.path.exists("Dockerfile"), "Dockerfile must exist"
    assert os.path.exists("seeds/01_runs.sql"), "seeds/01_runs.sql must exist"
    assert os.path.exists("demo/walkthrough.mp4"), "demo/walkthrough.mp4 must exist"
