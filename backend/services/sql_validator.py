import re
import sqlglot
from sqlglot import exp
from backend.database.db_manager import schema_description
from backend.core.config import get_settings
from backend.utils.exceptions import SQLValidationError

DENIED = {"read_csv", "read_csv_auto", "read_parquet", "read_json", "read_text", "read_blob", "write_csv", "write_blob", "write_text", "query", "query_table", "glob", "parquet_scan", "csv_scan", "httpfs", "sqlite_scan", "postgres_scan", "duckdb_external_file_cache", "pragma_version", "nextval", "setseed", "getenv"}

def validate_sql(sql: str) -> str:
    if not sql or len(sql) > 20_000:
        raise SQLValidationError("Enter a SQL query under 20,000 characters.")
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError("The SQL query could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SQLValidationError("Only one read-only SELECT query (including CTEs) is allowed.")
    tree = statements[0]
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for node in tree.walk():
        if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Command, exp.Copy, exp.Merge, exp.Transaction, exp.Use, exp.Set)):
            raise SQLValidationError("This query contains a prohibited operation.")
        if isinstance(node, exp.Func) and (node.sql_name().lower() in DENIED or getattr(node, "name", "").lower() in DENIED):
            raise SQLValidationError("This query uses a restricted function.")
        if isinstance(node, exp.Table):
            if node.db or node.catalog:
                raise SQLValidationError("Qualified catalog and schema access is not allowed.")
            name = node.name.lower()
            allowed = {x.lower() for x in schema_description()["tables"]}
            if name not in allowed and name not in cte_names:
                raise SQLValidationError(f"Table '{name}' is not available.")
    # DuckDB's read-only connection is the final write-access boundary. This visitor
    # rejects dangerous file/network functions and catalog-qualified references.
    normalized = tree.sql(dialect="duckdb")
    if re.search(r"\b(pg_catalog|information_schema|sqlite_master|duckdb_tables)\b", normalized, re.I):
        raise SQLValidationError("System catalog access is not allowed.")
    # Ask DuckDB's planner to resolve every referenced column and SQL construct.
    # DESCRIBE plans the SELECT without returning its rows.
    try:
        from backend.database.db_manager import connect
        connect().execute("DESCRIBE " + normalized).fetchall()
    except Exception as exc:
        raise SQLValidationError("The query references an invalid column or contains unsupported SQL.") from exc
    return normalized

def enforce_row_limit(sql: str) -> str:
    limit = get_settings().max_result_rows
    return f"SELECT * FROM ({sql}) AS querypilot_limited LIMIT {limit}"
