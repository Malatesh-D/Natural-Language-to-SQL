from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health(): assert client.get("/health").status_code == 200
def test_root(): assert client.get("/").json()["docs"] == "/docs"
def test_schema(): assert "customers" in client.get("/schema").json()["tables"]
def test_sql_endpoint(): assert client.post("/query/sql", json={"sql":"SELECT COUNT(*) AS total FROM customers"}).status_code == 200
def test_invalid_request(): assert client.post("/query", json={"question":"x"}).status_code == 422
def test_history_is_session_scoped():
    client.delete("/history", headers={"X-Session-ID":"test-a"})
    assert client.get("/history", headers={"X-Session-ID":"test-a"}).json()["items"] == []
    assert client.get("/history", headers={"X-Session-ID":"test-b"}).json()["items"] == []
