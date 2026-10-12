from functools import lru_cache
from pathlib import Path
import duckdb
from backend.core.config import get_settings

@lru_cache
def _read_connection():
    path = Path(get_settings().database_path)
    if not path.exists():
        raise RuntimeError("Sample database is missing. Run: python -m backend.database.init_db")
    return duckdb.connect(str(path), read_only=True)

def connect(read_only: bool = True):
    if read_only:
        return _read_connection()
    path = Path(get_settings().database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))

def close_read_connection():
    """Release the cached read-only connection before a database write."""
    if _read_connection.cache_info().currsize:
        _read_connection().close()
        _read_connection.cache_clear()

def schema_description() -> dict:
    con = connect()
    tables = {}
    for (name,) in con.execute("SHOW TABLES").fetchall():
        columns = con.execute(f"DESCRIBE {name}").fetchall()
        tables[name] = [{"name": c[0], "type": c[1], "description": _column_description(name, c[0])} for c in columns]
    return {"tables": tables, "relationships": [
        {"from": "orders.customer_id", "to": "customers.customer_id"},
        {"from": "order_items.order_id", "to": "orders.order_id"},
        {"from": "order_items.product_id", "to": "products.product_id"},
    ], "business_definitions": {"revenue": "Sum of orders.total_amount for completed orders unless the question specifies another status.", "order_items": "One row per product line within an order."}}

def _column_description(table: str, column: str) -> str:
    descriptions = {"email": "Customer email; avoid returning unless specifically requested.", "total_amount": "Order total in the currency used by the sample data.", "status": "Order lifecycle status."}
    return descriptions.get(column, "")
