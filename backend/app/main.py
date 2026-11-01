"""FastAPI app: CORS, lỗi dạng {detail}, lifespan khởi tạo DB."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.bootstrap_if_empty import init_and_bootstrap
from app.config import get_settings
from app.deps import get_db
from app.routers import alerts, auth, clean, config, devices, fund, history, ingest, statistics

logger = logging.getLogger("autubin")


class UTF8JSONResponse(JSONResponse):
    """Giữ tiếng Việt trong JSON thay vì escape \\uXXXX."""

    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


def _validation_detail(exc: RequestValidationError) -> str:
    messages: list[str] = []
    for err in exc.errors():
        loc = [
            str(part)
            for part in err.get("loc", [])
            if part not in ("body", "query", "header", "path")
        ]
        msg = err.get("msg", "Invalid value")
        messages.append(f"{'.'.join(loc)}: {msg}" if loc else str(msg))
    return "; ".join(messages) if messages else "Validation error"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    init_and_bootstrap()
    settings = get_settings()
    logger.info("AutoBin API ready db=%s", settings.db_path)
    yield


app = FastAPI(
    title="AutoBin API",
    version="1.0.0",
    description="REST API khớp SHARED_CONTRACT.md v1.0.0",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(clean.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(fund.router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return UTF8JSONResponse(status_code=exc.status_code, content={"detail": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return UTF8JSONResponse(status_code=400, content={"detail": _validation_detail(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return UTF8JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> dict[str, str]:
    conn.execute("SELECT 1")
    return {"status": "ok"}
