def recommend_chart(columns: list[str], rows: list[dict]) -> dict | None:
    if not rows or len(columns) < 2: return None
    numeric = [c for c in columns if isinstance(next((r.get(c) for r in rows if r.get(c) is not None), None), (int, float))]
    categorical = [c for c in columns if c not in numeric]
    if categorical and numeric:
        category, value = categorical[0], numeric[0]
        if len(rows) > 1:
            chart = "line" if any(word in category.lower() for word in ("date", "month", "year", "day")) else "bar"
            return {"type": chart, "x": category, "y": value}
    if len(numeric) >= 2: return {"type": "scatter", "x": numeric[0], "y": numeric[1]}
    return None
