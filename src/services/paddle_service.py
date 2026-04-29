from sqlite3 import IntegrityError

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
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
        payload=payload.model_dump(mode="json"),
    )
    session.add(event)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.info("Paddle webhook: duplicate event_id=%s, skipping", payload.event_id)
