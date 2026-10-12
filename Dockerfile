FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m backend.database.init_db
EXPOSE 8000 8501
CMD ["sh", "-c", "uvicorn backend.main:app --host 127.0.0.1 --port 8000 & exec streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-10000}"]
