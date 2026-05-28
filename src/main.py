import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.paddle import paddle_router
from api.user_api import user_router
from core.logger import register_logging
from services.license_worker import run_license_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = asyncio.Event()
    worker = asyncio.create_task(run_license_worker(stop))
    yield
    stop.set()
    await worker


app = FastAPI(lifespan=lifespan)

register_logging(app)
app.include_router(user_router, prefix="/api")
app.include_router(paddle_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok"}
