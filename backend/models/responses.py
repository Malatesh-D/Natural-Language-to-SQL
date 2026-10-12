from typing import Any
from pydantic import BaseModel

class QueryResponse(BaseModel):
    question: str | None = None
    sql: str
    explanation: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float
    chart: dict | None = None
