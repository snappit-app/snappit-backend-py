from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.user_api import user_router
from src.database import engine
from src.models.base import Base

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)

@app.get("/")
def root():
    return {"status": "ok"}
