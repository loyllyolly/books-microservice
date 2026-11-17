"""Main FastAPI application with endpoints, logging, and error handling."""
import logging
import sys
import time
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app import models, schemas, crud

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("microservice")

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Books Microservice API",
    description="RESTful микросервис для управления каталогом книг с PostgreSQL и Docker (ЛБ 14)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware for request logging and execution time
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Incoming request: {request.method} {request.url.path} from {client_ip}")

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Finished request: {request.method} {request.url.path} - "
            f"Status: {response.status_code} ({process_time:.2f}ms)"
        )
        return response
    except Exception as exc:
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Внутренняя ошибка сервера. Сервер обработал ошибку без падения."}
        )

# Custom validation error handler (Requirement 8)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{field}: {err.get('msg')}")
    logger.warning(f"Validation error on {request.method} {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Некорректные входные данные в запросе",
            "messages": errors
        }
    )

# Healthcheck
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "books-microservice"}

# 1. GET all books
@app.get(
    "/api/v1/books",
    response_model=List[schemas.BookResponse],
    summary="Получить список книг",
    tags=["Books"]
)
def read_books(
    skip: int = 0,
    limit: int = 50,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    db: Session = Depends(get_db)
):
    books = crud.get_books(db, skip=skip, limit=limit, author=author, genre=genre)
    logger.info(f"Retrieved {len(books)} books (skip={skip}, limit={limit})")
    return books

# 2. GET book by ID
@app.get(
    "/api/v1/books/{book_id}",
    response_model=schemas.BookResponse,
    summary="Получить книгу по ID",
    tags=["Books"]
)
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book_by_id(db, book_id=book_id)
    if not db_book:
        logger.warning(f"Book with id={book_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    return db_book

# 3. POST create book
@app.post(
    "/api/v1/books",
    response_model=schemas.BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить новую книгу",
    tags=["Books"]
)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    created = crud.create_book(db=db, book_in=book)
    logger.info(f"Book created: id={created.id}, title='{created.title}'")
    return created

# 4. PUT update book
@app.put(
    "/api/v1/books/{book_id}",
    response_model=schemas.BookResponse,
    summary="Обновить данные книги",
    tags=["Books"]
)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    updated = crud.update_book(db=db, book_id=book_id, book_in=book)
    if not updated:
        logger.warning(f"Book update failed: id={book_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    logger.info(f"Book updated: id={book_id}")
    return updated

# 5. DELETE book
@app.delete(
    "/api/v1/books/{book_id}",
    response_model=schemas.MessageResponse,
    summary="Удалить книгу",
    tags=["Books"]
)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    success = crud.delete_book(db=db, book_id=book_id)
    if not success:
        logger.warning(f"Book deletion failed: id={book_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена"
        )
    logger.info(f"Book deleted: id={book_id}")
    return {"detail": f"Книга с ID {book_id} успешно удалена"}
