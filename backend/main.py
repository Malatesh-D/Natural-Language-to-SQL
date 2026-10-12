from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.api.routes import router
from backend.core.logging_config import configure_logging
from backend.utils.exceptions import QueryPilotError

configure_logging()
app = FastAPI(title="QueryPilot AI API", version="1.0.0", description="Safe natural-language analytics for the QueryPilot sample database.")
app.include_router(router)

@app.get("/")
def root():
    return {
        "name": "QueryPilot AI API",
        "status": "running",
        "health": "/health",
        "docs": "/docs",
        "dashboard": "http://localhost:8501",
    }

@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "Invalid request. Check required fields and length limits."})
