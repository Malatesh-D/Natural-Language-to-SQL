import pytest
from backend.services.sql_validator import validate_sql, enforce_row_limit
from backend.utils.exceptions import SQLValidationError

@pytest.mark.parametrize("sql", ["SELECT city FROM customers", "WITH x AS (SELECT city FROM customers) SELECT city FROM x", "SELECT c.city, COUNT(*) AS n FROM customers c JOIN orders o ON c.customer_id=o.customer_id GROUP BY c.city", "SELECT * FROM products WHERE price > 10 ORDER BY price DESC"])
def test_valid_queries(sql): assert "SELECT" in validate_sql(sql).upper()

@pytest.mark.parametrize("sql", ["DELETE FROM customers", "DROP TABLE customers", "SELECT 1; SELECT 2", "SELECT * FROM missing_table", "SELECT * FROM read_csv('secret.csv')", "ATTACH 'x' AS y", "SELECT * FROM information_schema.tables"])
def test_rejects_unsafe_queries(sql):
    with pytest.raises(SQLValidationError): validate_sql(sql)

def test_invalid_column():
    with pytest.raises(Exception):
        # DuckDB rejects the nonexistent field at execution; no row is exposed.
        from backend.services.query_executor import execute_sql
        execute_sql("SELECT no_such_column FROM customers")

def test_limit_wrapper(): assert "LIMIT 1000" in enforce_row_limit("SELECT * FROM customers")
