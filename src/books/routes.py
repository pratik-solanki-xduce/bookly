from typing import List
from fastapi import Depends, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from src.books.models import Book
from src.books.schemas import BookCreateModel, BookUpdateModel
from src.books.service import BookService
from src.db.main import get_session
from src.auth.dependencies import AccessTokenBearer, RefreshTokenBearer
from src.auth.dependencies import RoleChecker

books_router = APIRouter()
book_service = BookService()
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(allowed_roles=["admin", "user"]))


@books_router.get("/", response_model=List[Book], dependencies=[role_checker])
async def get_all_books(
    session: AsyncSession = Depends(get_session),
    _: dict = Depends(access_token_bearer),
):
    books = await book_service.get_all_books(session)
    return books


@books_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=Book,
    dependencies=[role_checker],
)  # create a new book
async def create_book(
    book_data: BookCreateModel,
    session: AsyncSession = Depends(get_session),
    token_details: dict = Depends(access_token_bearer),
):
    new_book = await book_service.create_book(book_data, session)
    return new_book


@books_router.get("/{book_uid}", response_model=Book, dependencies=[role_checker])
async def get_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    _: dict = Depends(access_token_bearer),
):
    book = await book_service.get_book(book_uid, session)
    return book


@books_router.patch("/{book_uid}", dependencies=[role_checker])
async def update_book(
    book_uid: str,
    updated_book: BookUpdateModel,
    session: AsyncSession = Depends(get_session),
    _: dict = Depends(access_token_bearer),
):
    book = await book_service.update_book(book_uid, updated_book, session)
    return book


@books_router.delete(
    "/{book_uid}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[role_checker],
)  # delete a book
async def delete_book(
    book_uid: str,
    session: AsyncSession = Depends(get_session),
    _: dict = Depends(access_token_bearer),
):
    await book_service.delete_book(book_uid, session)
    return {"message": f"Book deleted"}
