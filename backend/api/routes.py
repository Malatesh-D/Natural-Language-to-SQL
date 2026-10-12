from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
import re
from pathlib import Path
import pandas as pd
import uuid
from backend.database.db_manager import schema_description, connect, close_read_connection
from backend.models.requests import QueryRequest, SQLRequest
from backend.models.responses import QueryResponse
from backend.services.llm_service import generate_sql
from backend.services.query_executor import execute_sql
from backend.services.visualization_service import recommend_chart
from backend.services.conversation_service import get_history, add_history, clear_history
from backend.utils.exceptions import QueryPilotError

router = APIRouter()
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

def _table_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    if not name or not re.match(r"^[a-z_]", name): name = "uploaded_" + name
    return name[:100]

@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...), table_name: str | None = Form(default=None)):
    """Import a CSV or Excel worksheet as a queryable DuckDB table."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(400, detail={"error": "Upload a CSV or Excel file (.csv, .xlsx, .xls)."})
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail={"error": "Files must be 25 MB or smaller."})
    try:
        from io import BytesIO, StringIO
        if suffix == ".csv":
            frame = pd.read_csv(StringIO(raw.decode("utf-8-sig")))
        else:
            frame = pd.read_excel(BytesIO(raw))
    except Exception as exc:
        raise HTTPException(400, detail={"error": "Could not read this file. Check that it is a valid CSV or Excel workbook."}) from exc
    if frame.empty or len(frame.columns) == 0:
        raise HTTPException(400, detail={"error": "The uploaded file has no data rows or columns."})
    if len(frame.columns) > 500:
        raise HTTPException(400, detail={"error": "Files may contain at most 500 columns."})
    target = _table_name(table_name or Path(file.filename or "dataset").stem)
    frame.columns = [str(col).strip() or f"column_{i + 1}" for i, col in enumerate(frame.columns)]
    close_read_connection()
    con = None
    try:
        con = connect(read_only=False)
        existing = {row[0].lower() for row in con.execute("SHOW TABLES").fetchall()}
        if target.lower() in existing:
            raise HTTPException(409, detail={"error": f"A table named '{target}' already exists. Choose another table name."})
        con.register("_upload_frame", frame)
        con.execute(f'CREATE TABLE "{target}" AS SELECT * FROM _upload_frame')
        con.unregister("_upload_frame")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, detail={"error": "Could not add this dataset to the database."}) from exc
    finally:
        if con is not None:
            con.close()
    return {"table": target, "rows": len(frame), "columns": len(frame.columns)}

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
