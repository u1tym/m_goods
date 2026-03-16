from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    goods: Mapped[list["Goods"]] = relationship(back_populates="media")


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    artist_persons: Mapped[list["ArtistPerson"]] = relationship(back_populates="artist")
    goods: Mapped[list["Goods"]] = relationship(back_populates="artist")


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    artist_persons: Mapped[list["ArtistPerson"]] = relationship(back_populates="person")


class ArtistPerson(Base):
    __tablename__ = "artist_persons"
    __table_args__ = (
        UniqueConstraint("artist_id", "person_id", name="uq_artist_person"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    artist: Mapped[Artist] = relationship(back_populates="artist_persons")
    person: Mapped[Person] = relationship(back_populates="artist_persons")


class Goods(Base):
    __tablename__ = "goods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"), nullable=False, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    release_date: Mapped[date] = mapped_column(Date, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    is_owned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    code_number: Mapped[str | None] = mapped_column(String, nullable=True)

    media: Mapped[Media] = relationship(back_populates="goods")
    artist: Mapped[Artist] = relationship(back_populates="goods")
    images: Mapped[list["GoodsImage"]] = relationship(back_populates="goods", cascade="all, delete-orphan")


class GoodsImage(Base):
    __tablename__ = "goods_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    goods_id: Mapped[int] = mapped_column(ForeignKey("goods.id"), nullable=False, index=True)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    image_type: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    goods: Mapped[Goods] = relationship(back_populates="images")

