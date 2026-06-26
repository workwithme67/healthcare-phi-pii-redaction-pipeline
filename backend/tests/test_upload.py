import io
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


def test_upload_text_success(client):
    payload = {"note": "Patient John Doe visited today for hypertension."}
    response = client.post("/api/upload-text", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "note_id" in data
    assert data["message"] == "Clinical note uploaded successfully"


def test_upload_text_empty_rejected(client):
    payload = {"note": "   "}
    response = client.post("/api/upload-text", json=payload)
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_upload_text_too_large_rejected(client):
    payload = {"note": "a" * 100001}
    response = client.post("/api/upload-text", json=payload)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


def test_upload_file_txt_success(client):
    file_content = b"Patient Jane Smith visited today for diabetes."
    file = {"file": ("patient_note.txt", file_content, "text/plain")}
    response = client.post("/api/upload-file", files=file)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "patient_note.txt"
    assert data["file_type"] == "TXT"
    assert data["status"] == "Uploaded"


def test_upload_file_pdf_success(client):
    file_content = b"%PDF-1.4 mock pdf content"
    file = {"file": ("patient_chart.pdf", file_content, "application/pdf")}
    response = client.post("/api/upload-file", files=file)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "patient_chart.pdf"
    assert data["file_type"] == "PDF"
    assert data["status"] == "Uploaded"


def test_upload_file_invalid_type_rejected(client):
    file_content = b"console.log('malicious script')"
    file = {"file": ("script.js", file_content, "application/javascript")}
    response = client.post("/api/upload-file", files=file)
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_file_too_large_rejected(client):
    large_content = b"a" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
    file = {"file": ("huge_note.txt", large_content, "text/plain")}
    response = client.post("/api/upload-file", files=file)
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]


def test_list_uploads(client):
    # Upload one text and one file
    client.post("/api/upload-text", json={"note": "Note text"})
    file_content = b"File text content"
    client.post("/api/upload-file", files={"file": ("note.txt", file_content, "text/plain")})

    response = client.get("/api/uploads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["filename"] == "note.txt"
    assert data[1]["filename"] == "Direct Note Upload"


def test_get_upload_details(client):
    # Upload text note
    resp = client.post("/api/upload-text", json={"note": "Patient Alice was here."})
    note_id = resp.json()["note_id"]

    response = client.get(f"/api/uploads/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["note_text"] == "Patient Alice was here."
    assert data["file_type"] == "TEXT"


def test_delete_upload(client):
    # Upload text note
    resp = client.post("/api/upload-text", json={"note": "Delete me."})
    note_id = resp.json()["note_id"]

    # Verify exists in list
    list_resp = client.get("/api/uploads")
    assert len(list_resp.json()) == 1

    # Delete
    del_resp = client.delete(f"/api/uploads/{note_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify deleted
    list_resp2 = client.get("/api/uploads")
    assert len(list_resp2.json()) == 0

    # Get details should return 404
    get_resp = client.get(f"/api/uploads/{note_id}")
    assert get_resp.status_code == 404
