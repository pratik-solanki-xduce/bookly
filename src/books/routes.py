from typing import List
from fastapi import HTTPException, status, APIRouter
from src.books.schema import Book, BookUpdate
from src.books.books_data import books

books_router = APIRouter()


@books_router.get("/", response_model=List[Book])  # get all books
async def get_all_books():
    return books


@books_router.post("/", status_code=status.HTTP_201_CREATED)  # create a new book
async def create_book(book: Book):
    new_book = Book(**book.model_dump(), id=len(books) + 1)
    books.append(new_book)
    return {"message": "Book created"}


@books_router.get("/{book_id}", response_model=Book)
async def get_book(book_id: int):
    for book in books:
        if book.id == book_id:
            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book not found")


@books_router.patch("/{book_id}")
async def update_book(book_id: int, updated_book: BookUpdate):
    for i, existing_book in enumerate(books):
        if existing_book.id == book_id:
            books[i] = Book(**updated_book.model_dump(), id=book_id)
            return books[i]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book not found")


@books_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)  # delete a book
async def delete_book(book_id: int):
    for book in books:
        if book.id == book_id:
            books.remove(book)
            return {"message": f"Book deleted"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book not found")
