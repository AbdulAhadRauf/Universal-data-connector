from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import health, data
from app.utils.logging import configure_logging
import logging

configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Data Connector",
    version="1.0.0",
    description="Unified interface for CRM, Support, and Analytics data sources optimized for LLM voice usage."
)

app.include_router(health.router)
app.include_router(data.router)


# -----------------------------
# Global Error Handler
# -----------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Something went wrong. Please try again later."
        },
    )
