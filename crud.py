from __future__ import annotations

from datetime import date
from typing import Iterable, List, Sequence
import base64
import binascii

from sqlalchemy import Select, distinct, select
from sqlalchemy.orm import Session

from models import Artist, ArtistPerson, Goods, GoodsImage, Media, Person
from schemas import (
    ArtistCreate,
    ArtistDetail,
    ArtistDetailPerson,
    ArtistSimple,
    ArtistUpdate,
    GoodsCreate,
    GoodsRelatedItem,
    GoodsUpdate,
    MediaCreate,
    MediaSimple,
    MediaUpdate,
    PersonCreate,
    PersonSimple,
)


class InvalidImageDataError(ValueError):
    """Raised when image_data is not valid Base64."""


def _decode_image_data_or_raise(image_data: str) -> bytes:
    try:
        return base64.b64decode(image_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise InvalidImageDataError("image_data must be a valid Base64 string") from exc


def _has_value(value: str | None) -> bool:
    return value is not None and value != ""


def list_persons(db: Session) -> List[PersonSimple]:
    stmt: Select[tuple[Person]] = select(Person).order_by(Person.id)
    persons: Sequence[Person] = db.execute(stmt).scalars().all()
    return [PersonSimple.model_validate(p) for p in persons]


def create_person(db: Session, data: PersonCreate) -> PersonSimple:
    person = Person(name=data.name)
    db.add(person)
    db.commit()
    db.refresh(person)
    return PersonSimple.model_validate(person)


def update_person(db: Session, person_id: int, name: str) -> PersonSimple:
    person: Person | None = db.get(Person, person_id)
    if person is None:
        raise ValueError("Person not found")
    person.name = name
    db.commit()
    db.refresh(person)
    return PersonSimple.model_validate(person)


def list_media(db: Session) -> List[MediaSimple]:
    stmt: Select[tuple[Media]] = select(Media).order_by(Media.id)
    media_rows: Sequence[Media] = db.execute(stmt).scalars().all()
    return [MediaSimple.model_validate(m) for m in media_rows]


def create_media(db: Session, data: MediaCreate) -> MediaSimple:
    media = Media(name=data.name)
    db.add(media)
    db.commit()
    db.refresh(media)
    return MediaSimple.model_validate(media)


def update_media(db: Session, media_id: int, name: str) -> MediaSimple:
    media: Media | None = db.get(Media, media_id)
    if media is None:
        raise ValueError("Media not found")
    media.name = name
    db.commit()
    db.refresh(media)
    return MediaSimple.model_validate(media)


def list_artists(db: Session) -> List[ArtistSimple]:
    stmt: Select[tuple[Artist]] = select(Artist).order_by(Artist.id)
    artists: Sequence[Artist] = db.execute(stmt).scalars().all()
    return [ArtistSimple.model_validate(a) for a in artists]


def create_artist(db: Session, data: ArtistCreate) -> ArtistSimple:
    artist = Artist(name=data.name)
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return ArtistSimple.model_validate(artist)


def _sync_artist_persons(db: Session, artist_id: int, desired_person_ids: Iterable[int]) -> None:
    desired_set = {int(pid) for pid in desired_person_ids}

    stmt: Select[tuple[ArtistPerson]] = select(ArtistPerson).where(ArtistPerson.artist_id == artist_id)
    current_links: Sequence[ArtistPerson] = db.execute(stmt).scalars().all()
    current_set = {link.person_id for link in current_links}

    to_add = desired_set - current_set
    to_remove = current_set - desired_set

    for person_id in to_add:
        db.add(ArtistPerson(artist_id=artist_id, person_id=person_id))

    if to_remove:
        stmt_delete: Select[tuple[ArtistPerson]] = select(ArtistPerson).where(
            ArtistPerson.artist_id == artist_id,
            ArtistPerson.person_id.in_(to_remove),
        )
        links_to_delete: Sequence[ArtistPerson] = db.execute(stmt_delete).scalars().all()
        for link in links_to_delete:
            db.delete(link)


def update_artist(db: Session, data: ArtistUpdate) -> ArtistSimple:
    artist: Artist | None = db.get(Artist, data.id)
    if artist is None:
        raise ValueError("Artist not found")

    artist.name = data.name
    _sync_artist_persons(db, artist_id=data.id, desired_person_ids=data.person_ids)

    db.commit()
    db.refresh(artist)
    return ArtistSimple.model_validate(artist)


def get_artist_detail(db: Session, artist_id: int) -> ArtistDetail:
    artist: Artist | None = db.get(Artist, artist_id)
    if artist is None:
        raise ValueError("Artist not found")

    stmt_links: Select[tuple[ArtistPerson]] = select(ArtistPerson).where(ArtistPerson.artist_id == artist_id)
    links: Sequence[ArtistPerson] = db.execute(stmt_links).scalars().all()
    person_ids = [link.person_id for link in links]

    persons: List[ArtistDetailPerson] = []
    if person_ids:
        stmt_persons: Select[tuple[Person]] = select(Person).where(Person.id.in_(person_ids))
        person_rows: Sequence[Person] = db.execute(stmt_persons).scalars().all()
        persons = [ArtistDetailPerson.model_validate(p) for p in person_rows]

    return ArtistDetail(name=artist.name, persons=persons)


def get_related_media_by_person(db: Session, person_id: int) -> List[MediaSimple]:
    stmt_artist_ids: Select[tuple[int]] = select(ArtistPerson.artist_id).where(ArtistPerson.person_id == person_id)
    artist_ids: List[int] = [row[0] for row in db.execute(stmt_artist_ids).all()]
    if not artist_ids:
        return []

    stmt_media_ids: Select[tuple[int]] = select(distinct(Goods.media_id)).where(
        Goods.artist_id.in_(artist_ids),
        Goods.is_deleted.is_(False),
    )
    media_ids: List[int] = [row[0] for row in db.execute(stmt_media_ids).all()]
    if not media_ids:
        return []

    stmt_media: Select[tuple[Media]] = select(Media).where(Media.id.in_(media_ids)).order_by(Media.id)
    media_rows: Sequence[Media] = db.execute(stmt_media).scalars().all()
    return [MediaSimple.model_validate(m) for m in media_rows]


def get_related_goods(
    db: Session,
    person_id: int,
    media_ids: Iterable[int],
) -> List[GoodsRelatedItem]:
    media_id_list = list({int(mid) for mid in media_ids})
    if not media_id_list:
        return []

    stmt_artist_ids: Select[tuple[int]] = select(ArtistPerson.artist_id).where(ArtistPerson.person_id == person_id)
    artist_ids: List[int] = [row[0] for row in db.execute(stmt_artist_ids).all()]
    if not artist_ids:
        return []

    stmt_goods: Select[tuple[Goods, Media, Artist, GoodsImage | None]] = (
        select(Goods, Media, Artist, GoodsImage)
        .join(Media, Goods.media_id == Media.id)
        .join(Artist, Goods.artist_id == Artist.id)
        .join(GoodsImage, GoodsImage.goods_id == Goods.id, isouter=True)
        .where(
            Goods.artist_id.in_(artist_ids),
            Goods.media_id.in_(media_id_list),
            Goods.is_deleted.is_(False),
        )
        .order_by(Goods.id, GoodsImage.display_order)
    )

    rows = db.execute(stmt_goods).all()

    result: List[GoodsRelatedItem] = []
    for goods, media, artist, image in rows:
        image_type_val: str | None = image.image_type if image else None
        if image and image.image_data is not None:
            image_data_val: str | None = base64.b64encode(image.image_data).decode("ascii")
        else:
            image_data_val = None
        result.append(
            GoodsRelatedItem(
                goods_id=goods.id,
                media_id=goods.media_id,
                artist_id=goods.artist_id,
                media_name=media.name,
                artist_name=artist.name,
                title=goods.title,
                release_date=goods.release_date,
                memo=goods.memo,
                is_owned=goods.is_owned,
                code_number=goods.code_number,
                image_type=image_type_val,
                image_data=image_data_val,
            )
        )

    return result


def get_related_artists_by_person(db: Session, person_id: int) -> List[ArtistSimple]:
    stmt_artist_ids: Select[tuple[int]] = select(ArtistPerson.artist_id).where(ArtistPerson.person_id == person_id)
    artist_ids: List[int] = [row[0] for row in db.execute(stmt_artist_ids).all()]
    if not artist_ids:
        return []

    stmt_artists: Select[tuple[Artist]] = select(Artist).where(Artist.id.in_(artist_ids)).order_by(Artist.id)
    artist_rows: Sequence[Artist] = db.execute(stmt_artists).scalars().all()
    return [ArtistSimple.model_validate(a) for a in artist_rows]


def get_goods_by_id(db: Session, goods_id: int) -> GoodsRelatedItem:
    stmt: Select[tuple[Goods, Media, Artist, GoodsImage | None]] = (
        select(Goods, Media, Artist, GoodsImage)
        .join(Media, Goods.media_id == Media.id)
        .join(Artist, Goods.artist_id == Artist.id)
        .join(GoodsImage, GoodsImage.goods_id == Goods.id, isouter=True)
        .where(Goods.id == goods_id)
        .order_by(GoodsImage.display_order)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise ValueError("Goods not found")
    goods, media, artist, image = row
    image_type_val: str | None = image.image_type if image else None
    if image and image.image_data is not None:
        image_data_val: str | None = base64.b64encode(image.image_data).decode("ascii")
    else:
        image_data_val = None
    return GoodsRelatedItem(
        goods_id=goods.id,
        media_id=goods.media_id,
        artist_id=goods.artist_id,
        media_name=media.name,
        artist_name=artist.name,
        title=goods.title,
        release_date=goods.release_date,
        memo=goods.memo,
        is_owned=goods.is_owned,
        code_number=goods.code_number,
        image_type=image_type_val,
        image_data=image_data_val,
    )


def create_goods(db: Session, data: GoodsCreate) -> int:
    release_date_value: date = data.release_date if data.release_date is not None else date.today()
    memo_value: str = data.memo if data.memo is not None else ""
    code_number_value: str = data.code_number if data.code_number is not None else ""
    goods = Goods(
        media_id=data.media_id,
        artist_id=data.artist_id,
        title=data.title,
        release_date=release_date_value,
        memo=memo_value,
        is_deleted=False,
        is_owned=data.is_owned if data.is_owned is not None else False,
        code_number=code_number_value,
    )
    db.add(goods)
    db.flush()

    if _has_value(data.image_type) and _has_value(data.image_data):
        decoded_image_data = _decode_image_data_or_raise(data.image_data)
        image = GoodsImage(
            goods_id=goods.id,
            image_data=decoded_image_data,
            image_type=data.image_type,
            display_order=1,
        )
        db.add(image)

    db.commit()
    return goods.id


def update_goods(db: Session, data: GoodsUpdate) -> None:
    goods: Goods | None = db.get(Goods, data.id)
    if goods is None:
        raise ValueError("Goods not found")

    goods.media_id = data.media_id
    goods.artist_id = data.artist_id
    goods.title = data.title
    if data.release_date is not None:
        goods.release_date = data.release_date
    goods.memo = data.memo if data.memo is not None else ""
    goods.is_owned = data.is_owned if data.is_owned is not None else False
    goods.code_number = data.code_number if data.code_number is not None else ""

    stmt_images: Select[tuple[GoodsImage]] = select(GoodsImage).where(GoodsImage.goods_id == goods.id)
    existing_images: Sequence[GoodsImage] = db.execute(stmt_images).scalars().all()

    if _has_value(data.image_type) and _has_value(data.image_data):
        decoded_image_data = _decode_image_data_or_raise(data.image_data)
        if existing_images:
            image = existing_images[0]
            image.image_type = data.image_type
            image.image_data = decoded_image_data
        else:
            db.add(
                GoodsImage(
                    goods_id=goods.id,
                    image_data=decoded_image_data,
                    image_type=data.image_type,
                    display_order=1,
                )
            )
    else:
        for image in existing_images:
            db.delete(image)

    db.commit()

