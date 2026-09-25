from pathlib import Path

from fastapi import APIRouter, Depends

from enterprise_rag.api.deps import get_settings
from enterprise_rag.api.schemas import HealthResponse
from enterprise_rag.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness and configuration check")
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Reports whether required configuration/data is present. Never calls the LLM, so it's free
    and fast to hit repeatedly (important on a free-tier Gemini key)."""
    gemini_configured = bool(settings.gemini_api_key)
    chroma_available = Path(settings.chroma_path).exists()
    sqlite_available = Path(settings.sqlite_path).exists()
    status = "ok" if (gemini_configured and chroma_available and sqlite_available) else "degraded"
    return HealthResponse(
        status=status,
        gemini_configured=gemini_configured,
        chroma_available=chroma_available,
        sqlite_available=sqlite_available,
    )
