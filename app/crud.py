"""CRUD operations for Book entity."""
from typing import List, Optional
from sqlalchemy.orm import Session
from app import models, schemas

def get_books(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    author: Optional[str] = None,
    genre: Optional[str] = None
) -> List[models.Book]:
    query = db.query(models.Book)
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.filter(models.Book.genre.ilike(f"%{genre}%"))
    return query.offset(skip).limit(limit).all()

def get_book_by_id(db: Session, book_id: int) -> Optional[models.Book]:
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def create_book(db: Session, book_in: schemas.BookCreate) -> models.Book:
    db_book = models.Book(**book_in.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def update_book(db: Session, book_id: int, book_in: schemas.BookUpdate) -> Optional[models.Book]:
    db_book = get_book_by_id(db, book_id)
    if not db_book:
        return None
    update_data = book_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int) -> bool:
    db_book = get_book_by_id(db, book_id)
    if not db_book:
        return False
    db.delete(db_book)
    db.commit()
    return True
