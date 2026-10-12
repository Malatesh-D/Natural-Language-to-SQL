import logging
from backend.core.config import get_settings
from backend.database.db_manager import schema_description
from backend.utils.exceptions import LLMConfigurationError, QueryPilotError

logger = logging.getLogger(__name__)

def generate_sql(question: str, context: str = "") -> tuple[str, str]:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise LLMConfigurationError("Gemini is not configured. Add GEMINI_API_KEY to your .env file.")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = f"""You generate safe read-only DuckDB SQL. Return JSON with keys sql and explanation.
Use exactly one SELECT statement. Never use external data sources, system catalogs, filesystem or network functions.
Never select customer emails unless asked. Use only this schema and relationships:
{schema_description()}
Business rule: completed orders count as sales/revenue by default.
Prior conversation context: {context or 'none'}
Question: {question}"""
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1))
        import json
        payload = json.loads(response.text or "{}")
        return payload["sql"], payload.get("explanation", "The query answers your question using the available business data.")
    except LLMConfigurationError:
        raise
    except Exception as exc:
        logger.exception("Gemini SQL generation failed")
        raise QueryPilotError("The AI service could not generate a query. Check the API key, quota, and network, then try again.") from exc
