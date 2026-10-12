from backend.services.query_executor import execute_sql

def test_select_and_join():
    result = execute_sql("SELECT c.city, COUNT(*) AS n FROM customers c JOIN orders o USING (customer_id) GROUP BY c.city ORDER BY n DESC")
    assert result["row_count"] > 0 and result["columns"] == ["city", "n"]

def test_empty_result():
    result = execute_sql("SELECT customer_id FROM customers WHERE customer_id < 0")
    assert result["row_count"] == 0
