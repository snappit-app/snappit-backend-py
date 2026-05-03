import json

from fastapi import HTTPException, Request, status
from paddle_billing.Notifications import Secret, Verifier
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.paddle._adapters import _PaddleRequest
from core.logger import logger
from core.settings import get_settings
from models.paddle.webhook_orm import PaddleWebhookEvent
from models.paddle.webhook_schema import (
    PaddleWebhookEventCreate,
    PaddleWebhookEventRead,
)


async def read_paddle_webhook_events(session: AsyncSession):
    stmt = select(PaddleWebhookEvent)
    result = await session.execute(stmt)
    events = result.scalars().all()
    return [PaddleWebhookEventRead.model_validate(u) for u in events]


async def verify_paddle_signature(request: Request):
    raw_body = await request.body()
    paddle_request = _PaddleRequest(
        body=raw_body,
        headers=request.headers,
    )
    secret = get_settings().paddle_secret_key
    integrity_check = Verifier().verify(paddle_request, Secret(secret))

    if not integrity_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Paddle signature",
        )
    return raw_body


async def create_webhook_event(session: AsyncSession, raw_body: bytes):
    try:
        payload = PaddleWebhookEventCreate.model_validate_json(raw_body)
    except ValidationError as exc:
        logger.warning("Paddle webhook: invalid payload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Paddle payload",
        ) from exc

    event = PaddleWebhookEvent(
        event_id=payload.event_id,
        event_type=payload.event_type,
        notification_id=payload.notification_id,
        occurred_at=payload.occurred_at,
        payload=json.loads(raw_body),
    )
    session.add(event)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.info("Paddle webhook: duplicate event_id=%s, skipping", payload.event_id)

    return None
