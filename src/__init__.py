from fastapi import FastAPI
from src.books.routes import books_router


version = "v1"

description = """
A REST API for a book review web service.

This REST API is able to:
- Create Read Update And delete books
- Add reviews to books
- Add tags to Books etc.
    """

version_prefix =f"/api/{version}"

app = FastAPI(
    title="Bookly",
    description=description,
    version=version,
    contact={
        "name": "Pratik Solanki",
        "url": "https://github.com/pratik-solanki-xduce",
        "email": "pratik.solanki@xduce.com",
    },
)

app.include_router(books_router, prefix=f"{version_prefix}/books", tags=["books"])
