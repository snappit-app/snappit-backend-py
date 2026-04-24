from fastapi import APIRouter

from src.database import session

paddle_router = APIRouter(prefix="/v1/paddle", tags=["paddle"])


@paddle_router.post("/webhook")
async def handlePaddleHook(session: session):
    return
