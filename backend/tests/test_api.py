import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import Base, get_db

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/api/v1/app/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "HealthTech" in data["project"]
    assert data["database"] == "connected"

def test_create_redaction_job(client):
    payload = {
        "text": "Patient Jane Doe, DOB 12/12/1990, has been diagnosed with influenza.",
        "filename": "note1.txt"
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["filename"] == "note1.txt"

def test_get_redaction_job(client):
    payload = {
        "text": "Patient Jane Doe, DOB 12/12/1990, has been diagnosed with influenza.",
        "filename": "note1.txt"
    }
    create_resp = client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["job_id"]

    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["original_text"] == payload["text"]

def test_list_redaction_jobs(client):
    # Create two jobs
    client.post("/api/v1/jobs", json={"text": "Note 1"})
    client.post("/api/v1/jobs", json={"text": "Note 2"})

    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

def test_get_statistics(client):
    client.post("/api/v1/jobs", json={"text": "Note 1"})
    
    response = client.get("/api/v1/jobs/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 1
    assert data["by_status"]["pending"] == 1
