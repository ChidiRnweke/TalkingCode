from fastapi import Request
from fastapi.responses import JSONResponse

from talkingcode.errors import AppError, InfraError, NotFoundError, UnauthorisedError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    match exc:
        case NotFoundError():
            return JSONResponse(
                status_code=404,
                content={
                    "error": "not_found",
                    "message": f"{exc.resource} not found",
                },
            )
        case UnauthorisedError():
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorised",
                    "message": str(exc),
                },
            )
        case InfraError():
            return JSONResponse(
                status_code=502,
                content={
                    "error": "infrastructure_error",
                    "message": str(exc),
                },
            )
        case _:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "unknown_error",
                    "message": str(exc),
                },
            )
