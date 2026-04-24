from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1 import api_v1_router
from core.api_response import error_payload, success_response
from core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Eureka MVP API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail and "detail" in exc.detail:
        payload = exc.detail
    else:
        payload = error_payload("http_error", exc.detail)
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    payload = error_payload("validation_error", exc.errors())
    return JSONResponse(status_code=422, content=payload)


@app.get("/api/v1/health")
async def health_check() -> dict:
    return success_response({"status": "ok"}, "Service is healthy.")


app.include_router(api_v1_router)
