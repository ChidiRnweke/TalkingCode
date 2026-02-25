"""Model list routes."""

from fastapi import APIRouter, Depends
from talkingcode.config import AppConfig
from talkingcode.dependencies import get_config
from talkingcode.models.api import ModelInfoResponse, ModelListResponse

router = APIRouter()


def _model_label(model_id: str) -> str:
    """Convert model ID to human-readable label."""
    # Strip provider prefix
    name = model_id.split("/", 1)[-1] if "/" in model_id else model_id
    # Remove common suffixes
    for suffix in ("-preview", "-001", "-latest"):
        name = name.removesuffix(suffix)
    # Replace hyphens/underscores with spaces and title case
    return name.replace("-", " ").replace("_", " ").title()


@router.get("/models")
async def list_models(config: AppConfig = Depends(get_config)) -> ModelListResponse:
    """Return curated model list with labels and default."""
    model_ids = [m.strip() for m in config.curated_models.split(",") if m.strip()]
    return ModelListResponse(
        models=[ModelInfoResponse(id=m, label=_model_label(m)) for m in model_ids],
        default=config.default_chat_model,
    )
