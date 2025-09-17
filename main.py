import logging
import time
from fastapi.staticfiles import StaticFiles
import uvicorn
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
from src.core import config
from src.core.logger import LOGGING
from src.db import redis, elastic
from src.db.database import db_session_manager
from contextlib import asynccontextmanager
from src.routers.urls import router as app_route
from src.routers.urls import http_exception_handler, request_validation_exception_handler, generic_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from elasticsearch import AsyncElasticsearch
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app = FastAPI(title=config.PROJECT_NAME)

# Подключение статики
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event('startup')
async def startup_event():
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, password=config.REDIS_PASSWORD)
    elastic.es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_URL}'])


@app.on_event('shutdown')
async def shutdown_event():
    await db_session_manager.close()
    await elastic.es.close()


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, generic_exception_handler)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}s"
        return response


app.add_middleware(ProcessTimeMiddleware)

app.include_router(app_route)


if __name__ == '__main__':

    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8090,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
