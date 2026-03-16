from __future__ import annotations

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session


load_dotenv()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def _build_database_url() -> str:
    host: str = os.getenv("DB_HOST", "localhost")
    port: str = os.getenv("DB_PORT", "5432")
    name: str = os.getenv("DB_NAME", "tamtdb")
    user: str = os.getenv("DB_USER", "tamtuser")
    password: str = os.getenv("DB_PASSWORD", "TAMTTAMT")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL: str = _build_database_url()

engine = create_engine(DATABASE_URL, echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

