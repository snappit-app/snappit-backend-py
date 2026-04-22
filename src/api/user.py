from fastapi import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import delete, select, update, insert
from sqlalchemy.exc import IntegrityError, NoResultFound

from src.database import session
from src.models.user.orm import UserCreate, UserRead, UserUpdate
from src.models.user.schema import User


user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.get('', response_model=list[UserRead])
async def getUsers(session: session):
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]

@user_router.get('/{user_id}', response_model=UserRead)
async def getUserById(user_id: int, session: session):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserRead.model_validate(user)

@user_router.delete('/{user_id}', response_model=int)
async def deleteUser(user_id: int, session: session):
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    stmt = delete(User).where(User.id == user_id)
    _ = await session.execute(stmt)
    await session.commit()
    return user_id

@user_router.post('', response_model=UserRead)
async def createUser(user_data: UserCreate, session: session):
    try:
        stmt = insert(User).values(**user_data.model_dump()).returning(User)
        result = await session.execute(stmt)
        user = result.scalar_one()
        await session.commit()
        return UserRead.model_validate(user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="User already exists or constraint violated")

@user_router.patch('/{user_id}', response_model=UserRead)
async def updateUser(user_id: int, user_data: UserUpdate, session: session):
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
