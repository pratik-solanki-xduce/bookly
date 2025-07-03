import asyncio
from datetime import timedelta
import email
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.auth.schemas import UserCreateModel, UserLoginModel
from src.auth.service import UserService
from src.db.main import get_session
from src.auth.utils import create_access_token, decode_token, verify_password

auth_router = APIRouter()
user_service = UserService()

REFRESH_TOKEN_EXPIRY = 2


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

@auth_router.post("/login")
async def login(user_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = user_data.email
    password = user_data.password
    
    user = await user_service._get_user_by_field("email", email, session)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User Not Found")
    
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Password")
    
    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_uid": str(user.uid),
            "role": user.role,
        }
    )

    refresh_token = create_access_token(
        user_data={"email": user.email, "user_uid": str(user.uid)},
        refresh=True,
        expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
    )

    return JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {"email": user.email, "uid": str(user.uid)},
        }
    )
