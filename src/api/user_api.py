from fastapi.routing import APIRouter

from core.database import session
from models.user.user_schema import UserCreate, UserRead, UserUpdate
from services import user_service

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("", response_model=list[UserRead])
async def get_users(session: session):
    return await user_service.get_users(session)


@user_router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(user_id: int, session: session):
    return await user_service.get_user_by_id(session, user_id)


@user_router.delete("/{user_id}", response_model=int)
async def delete_user(user_id: int, session: session):
    return await user_service.delete_user(session, user_id)


@user_router.post("", response_model=UserRead)
async def create_user(user_data: UserCreate, session: session):
    return await user_service.create_user(session, user_data)


@user_router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, user_data: UserUpdate, session: session):
    return await user_service.update_user(session, user_id, user_data)
