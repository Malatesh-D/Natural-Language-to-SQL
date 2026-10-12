from fastapi import APIRouter, Header, HTTPException
import uuid
from backend.database.db_manager import schema_description, connect
from backend.models.requests import QueryRequest, SQLRequest
from backend.models.responses import QueryResponse
from backend.services.llm_service import generate_sql
from backend.services.query_executor import execute_sql
from backend.services.visualization_service import recommend_chart
from backend.services.conversation_service import get_history, add_history, clear_history
from backend.utils.exceptions import QueryPilotError

router = APIRouter()

def _session(value: str | None) -> str:
    if value and len(value) <= 128 and value.isprintable(): return value
    return str(uuid.uuid4())

@router.get("/health")
def health():
    try:
        connect().execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(503, detail={"error": "Sample database is unavailable. Initialize it and restart the backend."}) from exc

@router.get("/schema")
def schema(): return schema_description()

@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, x_session_id: str | None = Header(default=None)):
    sid = _session(x_session_id)
    history = get_history(sid)
    context = "\n".join(f"Q: {h['question']}\nSQL: {h['sql']}" for h in history[-4:])
    try:
        sql, explanation = generate_sql(request.question, context)
        result = execute_sql(sql)
        answer = {"question": request.question, **result, "explanation": explanation, "chart": recommend_chart(result["columns"], result["rows"])}
        add_history(sid, {"question": request.question, "sql": result["sql"], "row_count": result["row_count"], "execution_time_ms": result["execution_time_ms"]})
        return answer
    except QueryPilotError as exc: raise HTTPException(400, detail={"error": str(exc)}) from exc

@router.post("/query/sql", response_model=QueryResponse)
def query_sql(request: SQLRequest):
    try:
        result = execute_sql(request.sql)
        return {**result, "explanation": "This is the result of your read-only SQL query.", "chart": recommend_chart(result["columns"], result["rows"])}
    except QueryPilotError as exc: raise HTTPException(400, detail={"error": str(exc)}) from exc

@router.get("/history")
def history(x_session_id: str | None = Header(default=None)): return {"items": get_history(_session(x_session_id))}

@router.delete("/history")
def delete_history(x_session_id: str | None = Header(default=None)):
    clear_history(_session(x_session_id)); return {"status": "cleared"}
