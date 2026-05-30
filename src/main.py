import asyncio
from contextlib import asynccontextmanager

import resend
from fastapi import FastAPI

from api.licnese.license_api import license_router
from api.paddle import paddle_router
from api.user_api import user_router
from core.logger import register_logging, setup_logging
from core.settings import get_settings
from services.license_worker import run_license_worker

setup_logging()
settings = get_settings()

resend.api_key = settings.resend_api_key


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
app.include_router(license_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok"}
