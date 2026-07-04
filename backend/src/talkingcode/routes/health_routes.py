"""Health check routes."""
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from talkingcode.dependencies import FactoryDep
from talkingcode.models.api import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, responses={500: {"model": HealthResponse}})
async def health_check(factory: FactoryDep) -> JSONResponse:
    controller = factory.get_health_controller()
    report = await controller.check_health()
    status_code = 500 if report.status == "failed" else 200
    return JSONResponse(
        content=jsonable_encoder(report),
        status_code=status_code,
    )
