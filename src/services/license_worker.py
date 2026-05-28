import asyncio

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from core.database import AsyncSessionLocal
from core.logger import logger
from models.paddle.webhook_orm import PaddleWebhookEvent, ProcessStatus
from services import license_service

BATCH_SIZE = 10
POLL_INTERVAL_SEC = 10
MAX_ATTEMPTS = 5


async def _process_event(event: PaddleWebhookEvent) -> None:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            code = await license_service.create_license(session, event)
            await session.execute(
                update(PaddleWebhookEvent)
                .where(PaddleWebhookEvent.id == event.id)
                .values(
                    process_status=ProcessStatus.PROCESSED,
                    processed_at=func.now(),
                )
            )
            logger.info(f"Created license: {code}")
    return


async def _claim_batch(session: AsyncSession) -> list[PaddleWebhookEvent]:
    stmt = (
        select(PaddleWebhookEvent)
        .where(
            PaddleWebhookEvent.process_status == ProcessStatus.PENDING,
            PaddleWebhookEvent.next_attempt_at <= func.now(),
        )
        .order_by(PaddleWebhookEvent.id)
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    events = await session.scalars(stmt)
    return list(events.all())


async def _tick() -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            events = await _claim_batch(session)

    if not events:
        return 0

    results = await asyncio.gather(
        *[_process_event(event) for event in events],
        return_exceptions=True,
    )

    failed = 0
    for event, result in zip(events, results):
        if isinstance(result, Exception):
            logger.exception("Failed to process event %s: %s", event.id, result, exc_info=result)
            failed += 1
    return len(events) - failed


async def run_license_worker(stop: asyncio.Event) -> None:
    logger.info("License worker started")
    while not stop.is_set():
        try:
            processed = await _tick()
        except Exception:
            logger.exception("License tick failed")
            processed = 0
        # если что-то нашли — сразу за следующей пачкой; иначе спим
        if processed == 0:
            try:
                await asyncio.wait_for(stop.wait(), timeout=POLL_INTERVAL_SEC)
            except TimeoutError:
                pass
    logger.info("License worker stopped")
