import logging
import sys
import time

from fastapi import Request
from fastapi.applications import FastAPI
from loguru import logger

from core.settings import get_settings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

_INTERCEPTED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "sqlalchemy.engine",
)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # ищем кадр, из которого реально пришёл лог, чтобы name/line были верными
        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    settings = get_settings()

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=LOG_FORMAT,
        backtrace=True,
        diagnose=False,
    )

    handler = InterceptHandler()
    logging.basicConfig(handlers=[handler], level=0, force=True)
    for name in _INTERCEPTED_LOGGERS:
        std_logger = logging.getLogger(name)
        std_logger.handlers = [handler]
        std_logger.propagate = False


def register_logging(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        method = request.method
        url = str(request.url)

        logger.info("➡️ {} {}", method, url)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("❌ Error on {} {}", method, url)
            raise

        process_time = (time.time() - start_time) * 1000

        logger.info(
            "⬅️ {} {} | status={} | time={:.2f}ms",
            method,
            url,
            response.status_code,
            process_time,
        )

        return response
