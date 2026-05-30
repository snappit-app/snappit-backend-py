import asyncio

from fastapi import APIRouter, status
from fastapi.param_functions import Depends
from fastapi.requests import Request
from sqlalchemy import select

from core.database import session
from core.paddle_client import get_paddle_client
from models.license.license_orm import License
from services import paddle_service

paddle_router = APIRouter(prefix="/v1/paddle", tags=["paddle"])


@paddle_router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def handle_paddle_webhook_event(
    _: Request,
    session: session,
    raw_body: bytes = Depends(paddle_service.verify_paddle_signature),
):
    await paddle_service.create_webhook_event(session, raw_body)
    return None


@paddle_router.get("/webhook")
async def read_paddle_webhook_events(session: session):
    return await paddle_service.read_paddle_webhook_events(session)


@paddle_router.get("/get_paddle_customer")
async def get_paddle_customer(session: session):
    paddle = get_paddle_client()
    return await asyncio.to_thread(
        paddle.customers.get, "ctm_01khgvv75w70dgj6dv5250qqm5"
    )
