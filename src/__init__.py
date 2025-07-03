from fastapi import FastAPI
from src.books.routes import books_router
from src.auth.routes import auth_router
from contextlib import asynccontextmanager
from src.db.main import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await init_db()
    print("Database initialized")
    yield



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
    lifespan=lifespan,
    contact={
        "name": "Pratik Solanki",
        "url": "https://github.com/pratik-solanki-xduce",
        "email": "pratik.solanki@xduce.com",
    },
)

app.include_router(books_router, prefix=f"{version_prefix}/books", tags=["books"])
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["auth"])