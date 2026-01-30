import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database import init_db
from src.exceptions import BusinessError
from src.routers import clients, regions
from src.schemas.error import ErrorDetail, ErrorResponse
from src.seed import seed_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(lifespan=lifespan)


def _error_name_from_class(cls: type) -> str:
    """PascalCase → UPPER_SNAKE_CASE, например ClientAlreadyExists → CLIENT_ALREADY_EXISTS."""
    name = cls.__name__
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Ошибки валидации Pydantic → единый формат: error_name, message, details (где и что)."""
    errors = [
        ErrorDetail(
            field=".".join(str(loc) for loc in err["loc"]),
            message=err.get("msg", ""),
        )
        for err in exc.errors()
    ]
    body = ErrorResponse(
        error_name="VALIDATION_ERROR",
        message="Ошибка валидации",
        errors=errors,
    )
    return JSONResponse(
        status_code=422,
        content=body.model_dump(by_alias=True),
    )


@app.exception_handler(BusinessError)
async def business_error_handler(
    _request: Request,
    exc: BusinessError,
) -> JSONResponse:
    """Любая бизнес-ошибка (наследник BusinessError) → единый формат ответа."""
    error_name = _error_name_from_class(exc.__class__)
    body = ErrorResponse(
        error_name=error_name,
        message=exc.message,
        errors=None,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(by_alias=True),
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(regions.router, prefix="/api/regions", tags=["regions"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
