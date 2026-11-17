"""Pydantic schemas for request validation and response serialization."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Название книги")
    author: str = Field(..., min_length=1, max_length=255, description="Автор книги")
    genre: Optional[str] = Field(None, max_length=100, description="Жанр книги")
    publication_year: Optional[int] = Field(None, ge=1000, le=2100, description="Год издания (1000-2100)")
    description: Optional[str] = Field(None, description="Краткое описание")

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    description: Optional[str] = None

class BookResponse(BookBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    detail: str
