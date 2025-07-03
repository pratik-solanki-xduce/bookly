import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserCreateModel
from src.auth.service import UserService
from src.db.main import get_session

auth_router = APIRouter()
user_service = UserService()


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(user_data: UserCreateModel, session: AsyncSession = Depends(get_session)):
    
    email_exists, username_exists = await asyncio.gather(
        user_service._user_exists_by_field("email", user_data.email, session),
        user_service._user_exists_by_field("username", user_data.username, session)
    )

    if email_exists or username_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    new_user = await user_service.create_user(user_data, session)
    return new_user
