from unittest.mock import patch
from types import SimpleNamespace
from backend.services.llm_service import generate_sql

def test_gemini_client_generation(monkeypatch):
    from backend.core.config import get_settings
    monkeypatch.setattr(get_settings(), "gemini_api_key", "test-key")
    fake_client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: SimpleNamespace(text='{"sql":"SELECT city FROM customers","explanation":"Cities"}')))
    with patch("google.genai.Client", return_value=fake_client):
        sql, explanation = generate_sql("List cities")
    assert sql.startswith("SELECT") and explanation == "Cities"
