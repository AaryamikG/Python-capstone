from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from enterprise_rag.api.deps import get_settings
from enterprise_rag.api.routes import health, manager, qualitative, quantitative
from enterprise_rag.logging_config import configure_logging, get_logger

configure_logging(get_settings().log_level)
logger = get_logger(__name__)

app = FastAPI(
    title="Enterprise Documentation Assistant API",
    description="Manager, qualitative RAG, and quantitative NL-to-SQL agents over enterprise documentation.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(manager.router)
app.include_router(qualitative.router)
app.include_router(quantitative.router)


@app.exception_handler(Exception)
async def log_unhandled_exceptions(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_api_exception",
        exc_info=True,
        extra={"event_data": {"path": request.url.path}},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
