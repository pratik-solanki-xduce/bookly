from fastapi import FastAPI
from src.books.routes import books_router
from src.auth.routes import auth_router
from src.reviews.routes import review_router
from src.tags.routes import tags_router
from src.errors import register_all_errors
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.middleware import register_middleware


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

version_prefix = f"/api/{version}"

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
    terms_of_service="https://example.com/tos",
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}/docs",
    redoc_url=f"{version_prefix}/redoc"
)

register_all_errors(app)

register_middleware(app)

app.include_router(books_router, prefix=f"{version_prefix}/books", tags=["books"])
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["auth"])
app.include_router(review_router, prefix=f"{version_prefix}/reviews", tags=["reviews"])
app.include_router(tags_router, prefix=f"{version_prefix}/tags", tags=["tags"])
