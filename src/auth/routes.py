import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.auth.schemas import (
    PasswordResetConfirmModel,
    PasswordResetRequestModel,
    UserBooksModel,
    UserCreateModel,
    UserLoginModel,
)
from src.auth.service import UserService
from src.config import Config
from src.db.main import get_session
from src.auth.utils import (
    create_access_token,
    create_url_safe_token,
    decode_token,
    decode_url_safe_token,
    generate_passwd_hash,
    verify_password,
)
from src.auth.dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    get_current_user,
    RoleChecker,
)
from src.db.redis import add_jti_to_blocklist
from src.errors import InvalidCredentials, InvalidToken, UserAlreadyExists, UserNotFound
from src.auth.schemas import EmailModel
from src.mail import create_message, mail

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(allowed_roles=["admin", "user"])

REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses

    html = "<h1>Welcome to the app</h1>"
    subject = "Welcome to our app"

    message = create_message(emails, subject, html)
    await mail.send_message(message)

    return {"message": "Email sent successfully"}


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreateModel, session: AsyncSession = Depends(get_session)
):

    email_exists, username_exists = await asyncio.gather(
        user_service._user_exists_by_field("email", user_data.email, session),
        user_service._user_exists_by_field("username", user_data.username, session),
    )

    if email_exists or username_exists:
        raise UserAlreadyExists()
    new_user = await user_service.create_user(user_data, session)
    token = create_url_safe_token({"email": user_data.email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """

    emails = [user_data.email]

    subject = "Verify Your email"

    # send_email.delay(emails, subject, html)
    message = create_message(emails, subject, html)
    await mail.send_message(message)

    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service._get_user_by_field("email", user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"message": "Account verified successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during verification"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(
    user_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    email = user_data.email
    password = user_data.password

    user = await user_service._get_user_by_field("email", email, session)

    if not user:
        raise InvalidCredentials()

    if not verify_password(password, user.password_hash):
        raise InvalidCredentials()

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


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise InvalidToken()


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )


@auth_router.get("/me", response_model=UserBooksModel)
async def get_current_user(
    user=Depends(get_current_user), _: bool = Depends(role_checker)
):
    return user


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message = f"""
    <h1>Reset Your Password</h1>
    <p>Please click this <a href="{link}">link</a> to Reset Your Password</p>
    """
    subject = "Reset Your Password"

    # send_email.delay([email], subject, html_message)
    message = create_message([email], subject, html_message)
    await mail.send_message(message)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service._get_user_by_field("email", user_email, session)

        if not user:
            raise UserNotFound()

        passwd_hash = generate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
