from fastapi import HTTPException
from sqlalchemy import delete, select, update, insert
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user.orm import UserCreate, UserRead, UserUpdate
from src.models.user.schema import User


async def get_users(session: AsyncSession) -> list[UserRead]:
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]


async def get_user_by_id(session: AsyncSession, user_id: int) -> UserRead:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserRead.model_validate(user)


async def delete_user(session: AsyncSession, user_id: int) -> int:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    stmt = delete(User).where(User.id == user_id)
    _ = await session.execute(stmt)
    await session.commit()
    return user_id


async def create_user(session: AsyncSession, user_data: UserCreate) -> UserRead:
    try:
        stmt = insert(User).values(**user_data.model_dump()).returning(User)
        result = await session.execute(stmt)
        user = result.scalar_one()
        await session.commit()
        return UserRead.model_validate(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="User already exists or constraint violated")


async def update_user(session: AsyncSession, user_id: int, user_data: UserUpdate) -> UserRead:
    try:
        stmt = update(User).where(User.id == user_id).values(**user_data.model_dump()).returning(User)
        result = await session.execute(stmt)
        user = result.scalar_one()
        await session.commit()
        return UserRead.model_validate(user)
    except NoResultFound:
        await session.rollback()
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Constraint violated")
