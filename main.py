from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from crud import (
    create_artist,
    create_goods,
    create_media,
    create_person,
    get_artist_detail,
    get_goods_by_id,
    get_related_artists_by_person,
    get_related_goods,
    get_related_media_by_person,
    list_artists,
    list_media,
    list_persons,
    update_artist,
    update_goods,
    update_media,
    update_person,
)
from database import get_db
from schemas import (
    ArtistCreate,
    ArtistDetail,
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
    PersonUpdate,
    RelatedArtistRequest,
    RelatedGoodsRequest,
    RelatedMediaRequest,
)

app = FastAPI(title="m_goods API")


@app.get("/persons", response_model=List[PersonSimple])
def get_persons(db: Session = Depends(get_db)) -> List[PersonSimple]:
    """1) person一覧取得."""
    return list_persons(db)


@app.post("/persons", response_model=PersonSimple, status_code=status.HTTP_201_CREATED)
def add_person(data: PersonCreate, db: Session = Depends(get_db)) -> PersonSimple:
    """5) person追加."""
    return create_person(db, data)


@app.put("/persons/{person_id}", response_model=PersonSimple)
def update_person_endpoint(person_id: int, data: PersonUpdate, db: Session = Depends(get_db)) -> PersonSimple:
    """6) person更新."""
    if person_id != data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path id and body id mismatch")
    try:
        return update_person(db, person_id=person_id, name=data.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/persons/related-media", response_model=List[MediaSimple])
def get_related_media(request: RelatedMediaRequest, db: Session = Depends(get_db)) -> List[MediaSimple]:
    """2) 関連media一覧取得."""
    return get_related_media_by_person(db, person_id=request.person_id)


@app.post("/persons/related-goods", response_model=List[GoodsRelatedItem])
def get_related_goods_endpoint(request: RelatedGoodsRequest, db: Session = Depends(get_db)) -> List[GoodsRelatedItem]:
    """3) 関連goods一覧取得."""
    return get_related_goods(db, person_id=request.person_id, media_ids=request.media_ids)


@app.post("/persons/related-artists", response_model=List[ArtistSimple])
def get_related_artists_endpoint(
    request: RelatedArtistRequest,
    db: Session = Depends(get_db),
) -> List[ArtistSimple]:
    """4) 関連artist一覧取得."""
    return get_related_artists_by_person(db, person_id=request.person_id)


@app.get("/artists", response_model=List[ArtistSimple])
def get_artists(db: Session = Depends(get_db)) -> List[ArtistSimple]:
    """7) artist一覧取得."""
    return list_artists(db)


@app.get("/artists/{artist_id}", response_model=ArtistDetail)
def get_artist_info(artist_id: int, db: Session = Depends(get_db)) -> ArtistDetail:
    """8) artist情報取得."""
    try:
        return get_artist_detail(db, artist_id=artist_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/artists", response_model=ArtistSimple, status_code=status.HTTP_201_CREATED)
def add_artist(data: ArtistCreate, db: Session = Depends(get_db)) -> ArtistSimple:
    """9) artist追加."""
    return create_artist(db, data)


@app.put("/artists/{artist_id}", response_model=ArtistSimple)
def update_artist_endpoint(artist_id: int, data: ArtistUpdate, db: Session = Depends(get_db)) -> ArtistSimple:
    """10) artist更新."""
    if artist_id != data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path id and body id mismatch")
    try:
        return update_artist(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/media", response_model=List[MediaSimple])
def get_media_list(db: Session = Depends(get_db)) -> List[MediaSimple]:
    """11) media一覧取得."""
    return list_media(db)


@app.post("/media", response_model=MediaSimple, status_code=status.HTTP_201_CREATED)
def add_media(data: MediaCreate, db: Session = Depends(get_db)) -> MediaSimple:
    """12) media追加."""
    return create_media(db, data)


@app.put("/media/{media_id}", response_model=MediaSimple)
def update_media_endpoint(media_id: int, data: MediaUpdate, db: Session = Depends(get_db)) -> MediaSimple:
    """13) media更新処理."""
    if media_id != data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path id and body id mismatch")
    try:
        return update_media(db, media_id=media_id, name=data.name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.get("/goods/{goods_id}", response_model=GoodsRelatedItem)
def get_goods(goods_id: int, db: Session = Depends(get_db)) -> GoodsRelatedItem:
    """goods 1件取得."""
    try:
        return get_goods_by_id(db, goods_id=goods_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/goods", status_code=status.HTTP_201_CREATED)
def add_goods(data: GoodsCreate, db: Session = Depends(get_db)) -> dict:
    """14) goods追加."""
    if not data.media_id or not data.artist_id or not data.title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="media_id, artist_id, title are required")
    goods_id: int = create_goods(db, data)
    return {"id": goods_id}


@app.put("/goods/{goods_id}")
def update_goods_endpoint(goods_id: int, data: GoodsUpdate, db: Session = Depends(get_db)) -> dict:
    """15) goods更新."""
    if goods_id != data.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path id and body id mismatch")
    if not data.media_id or not data.artist_id or not data.title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="media_id, artist_id, title are required")
    try:
        update_goods(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"id": goods_id}

