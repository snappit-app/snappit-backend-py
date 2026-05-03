from fastapi import FastAPI

from api.paddle import paddle_router
from api.user_api import user_router
from core.logger import register_logging

app = FastAPI()

register_logging(app)
app.include_router(user_router, prefix="/api")
app.include_router(paddle_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok"}
