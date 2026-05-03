from fastapi import APIRouter, status
from fastapi.param_functions import Depends
from fastapi.requests import Request

from core.database import session
from services import paddle_service

paddle_router = APIRouter(prefix="/v1/paddle", tags=["paddle"])


@paddle_router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def handle_paddle_webhook_event(
    _: Request,
    session: session,
    raw_body: bytes = Depends(paddle_service.verify_paddle_signature),
):
    return await paddle_service.create_webhook_event(session, raw_body)


@paddle_router.get("/webhook")
async def read_paddle_webhook_events(session: session):
    return await paddle_service.read_paddle_webhook_events(session)
