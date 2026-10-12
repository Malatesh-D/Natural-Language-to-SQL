import time
import threading
from pathlib import Path
import duckdb
from backend.core.config import get_settings
from backend.services.sql_validator import validate_sql, enforce_row_limit
from backend.core.config import get_settings
from backend.utils.exceptions import QueryPilotError

def execute_sql(sql: str) -> dict:
    safe_sql = enforce_row_limit(validate_sql(sql))
    start = time.perf_counter()
    settings = get_settings()
    con = duckdb.connect(str(Path(settings.database_path)), read_only=True)
    timed_out = threading.Event()
    def interrupt():
        timed_out.set()
        try: con.interrupt()
        except Exception: pass
    timer = threading.Timer(settings.query_timeout_seconds, interrupt)
    timer.daemon = True
    timer.start()
    try:
        con.execute(safe_sql)
        frame = con.fetch_df()
        seconds = time.perf_counter() - start
        return {"sql": validate_sql(sql), "columns": list(frame.columns), "rows": frame.where(frame.notna(), None).to_dict(orient="records"), "row_count": len(frame), "execution_time_ms": round(seconds*1000, 2)}
    except duckdb.Error as exc:
        if timed_out.is_set():
            raise QueryPilotError("The query exceeded the configured time limit. Try a simpler question or narrower filter.") from exc
        raise QueryPilotError("The database could not run that query. Check table names, columns, and SQL syntax.") from exc
    finally:
        timer.cancel()
        con.close()
