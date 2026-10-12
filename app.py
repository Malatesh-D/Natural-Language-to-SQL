import uuid
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from backend.core.config import get_settings

st.set_page_config(page_title="QueryPilot AI", page_icon="✦", layout="wide")
settings = get_settings()
api = settings.backend_url.rstrip("/")
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
headers = {"X-Session-ID": st.session_state.session_id}

def api_call(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, api + path, headers=headers, timeout=45, **kwargs)
        data = response.json()
        if not response.ok: raise RuntimeError(data.get("detail", {}).get("error", "The request could not be completed."))
        return data
    except requests.RequestException as exc:
        raise RuntimeError("Backend unavailable. Start the FastAPI server and try again.") from exc

st.markdown("<style>.block-container{padding-top:2rem;max-width:1400px} [data-testid='stSidebar']{background:#101a2b}</style>", unsafe_allow_html=True)
with st.sidebar:
    st.title("✦ QueryPilot AI")
    st.caption("Ask your business data in plain English")
    try:
        health = api_call("GET", "/health")
        st.success("Database connected")
    except RuntimeError as exc:
        st.error(str(exc)); health = None
    st.markdown("### Your data")
    with st.expander("Upload a dataset"):
        upload = st.file_uploader("CSV or Excel file", type=["csv", "xlsx", "xls"], help="Files up to 25 MB. Excel imports the first worksheet.")
        dataset_name = st.text_input("Table name (optional)", placeholder="Use the filename")
        if st.button("Add to database", disabled=upload is None, use_container_width=True):
            try:
                payload = {"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")}
                form = {"table_name": dataset_name} if dataset_name.strip() else {}
                added = api_call("POST", "/datasets/upload", files=payload, data=form)
                st.success(f"Added **{added['table']}** with {added['rows']:,} rows and {added['columns']} columns.")
                st.rerun()
            except RuntimeError as exc:
                st.error(str(exc))
    if health:
        try:
            schema = api_call("GET", "/schema")
            for table, cols in schema["tables"].items():
                with st.expander(table.replace("_", " ").title()): st.caption(", ".join(c["name"] for c in cols))
        except RuntimeError: pass
    st.markdown("### Try asking")
    examples = ["Show the top 5 customers by total spending", "What is revenue by product category?", "Show monthly sales for completed orders", "Which cities have the most customers?"]
    for ex in examples:
        if st.button(ex, use_container_width=True): st.session_state.question = ex
    st.caption("Gemini: " + ("configured" if settings.gemini_api_key else "API key required"))
    if st.button("Clear conversation", use_container_width=True):
        api_call("DELETE", "/history"); st.session_state.pop("last_result", None); st.rerun()

st.title("Ask Your Database")
st.write("Turn a business question into a safe query and an answer you can explore.")
with st.form("ask", clear_on_submit=False):
    question = st.text_area("What would you like to know?", key="question", placeholder="For example: Show the top 5 customers by total spending", height=95)
    submitted = st.form_submit_button("✦ Ask QueryPilot", type="primary")
if submitted:
    if len(question.strip()) < 3: st.warning("Enter a question with a little more detail.")
    else:
        with st.spinner("Understanding your question and querying the database…"):
            try: st.session_state.last_result = api_call("POST", "/query", json={"question": question})
            except RuntimeError as exc: st.error(str(exc))

result = st.session_state.get("last_result")
try:
    conversation_items = api_call("GET", "/history")["items"]
except RuntimeError:
    conversation_items = []
if conversation_items:
    with st.expander("Recent questions", expanded=False):
        for item in reversed(conversation_items):
            st.markdown(f"**{item['question']}**  ")
            st.caption(f"{item['row_count']} rows · {item['execution_time_ms']:.1f} ms")

if result:
    st.divider()
    st.markdown(f"#### {result.get('question', 'SQL query result')}")
    m1, m2 = st.columns(2); m1.metric("Rows returned", result["row_count"]); m2.metric("Query time", f"{result['execution_time_ms']:.1f} ms")
    with st.expander("Generated SQL", expanded=True): st.code(result["sql"], language="sql")
    st.info(result["explanation"])
    frame = pd.DataFrame(result["rows"], columns=result["columns"])
    if frame.empty: st.warning("The query ran successfully but returned no rows.")
    else:
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", frame.to_csv(index=False).encode("utf-8"), "querypilot-results.csv", "text/csv")
        chart = result.get("chart")
        if chart:
            choices = [chart["type"], "bar", "line", "scatter"]
            chart_type = st.selectbox("Explore as", list(dict.fromkeys(choices)))
            if chart_type == "line": fig = px.line(frame, x=chart["x"], y=chart["y"])
            elif chart_type == "scatter": fig = px.scatter(frame, x=chart["x"], y=chart["y"])
            else: fig = px.bar(frame, x=chart["x"], y=chart["y"])
            st.plotly_chart(fig, use_container_width=True)

with st.expander("Run read-only SQL"):
    sql_text = st.text_area("SQL", placeholder="SELECT city, COUNT(*) AS customers FROM customers GROUP BY city ORDER BY customers DESC", height=110)
    if st.button("Run SQL"):
        try: st.session_state.sql_result = api_call("POST", "/query/sql", json={"sql": sql_text})
        except RuntimeError as exc: st.error(str(exc))
    raw = st.session_state.get("sql_result")
    if raw:
        st.code(raw["sql"], language="sql"); st.dataframe(pd.DataFrame(raw["rows"]), use_container_width=True, hide_index=True)
