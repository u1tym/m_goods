from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PersonBase(BaseModel):
    name: str = Field(..., max_length=255)


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    id: int
    name: str = Field(..., max_length=255)


class PersonSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MediaBase(BaseModel):
    name: str = Field(..., max_length=255)


class MediaCreate(MediaBase):
    pass


class MediaUpdate(BaseModel):
    id: int
    name: str = Field(..., max_length=255)


class MediaSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ArtistBase(BaseModel):
    name: str = Field(..., max_length=255)


class ArtistCreate(ArtistBase):
    pass


class ArtistUpdate(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    person_ids: List[int] = Field(default_factory=list)


class ArtistSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ArtistDetailPerson(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ArtistDetail(BaseModel):
    name: str
    persons: List[ArtistDetailPerson]


class GoodsImageInfo(BaseModel):
    image_type: Optional[str] = None
    image_data: Optional[bytes] = None


class GoodsBase(BaseModel):
    media_id: int
    artist_id: int
    title: str
    release_date: Optional[date] = None
    memo: Optional[str] = None
    is_owned: Optional[bool] = False
    code_number: Optional[str] = None
    image_type: Optional[str] = None
    image_data: Optional[bytes] = None


class GoodsCreate(GoodsBase):
    pass


class GoodsUpdate(GoodsBase):
    id: int


class GoodsRelatedItem(BaseModel):
    goods_id: int
    media_id: int
    artist_id: int
    media_name: str
    artist_name: str
    title: str
    release_date: date
    memo: Optional[str]
    is_owned: bool
    code_number: Optional[str]
    image_type: Optional[str]
    image_data: Optional[bytes]


class RelatedMediaRequest(BaseModel):
    person_id: int


class RelatedGoodsRequest(BaseModel):
    person_id: int
    media_ids: List[int]


class RelatedArtistRequest(BaseModel):
    person_id: int

