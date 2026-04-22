from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.user import user_router
from src.database import engine
from src.models.base import Base
from src.models.user import schema  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
def root():
    return {"status": "ok"}
