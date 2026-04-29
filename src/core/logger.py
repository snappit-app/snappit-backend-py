import logging
import time

from fastapi import Request
from fastapi.applications import FastAPI

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)


def register_logging(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        method = request.method
        url = str(request.url)

        logger.info(f"➡️ {method} {url}")

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"❌ Error on {method} {url}: {e}")
            raise

        process_time = (time.time() - start_time) * 1000

        logger.info(
            f"⬅️ {method} {url} | status={response.status_code} | time={process_time:.2f}ms"
        )

        return response
