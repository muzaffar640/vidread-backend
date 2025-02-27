from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class VisibilityLevel(str, Enum):
    PRIVATE = "Private"
    PUBLIC = "Public"
    SHARED = "Shared"


class PermissionType(str, Enum):
    READ = "Read"
    EDIT = "Edit"


class SharedWith(BaseModel):
    user_id: str
    permission: PermissionType


class ReadingListItem(BaseModel):
    video_id: str
    added_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    order: int


class ReadingListBase(BaseModel):
    title: str
    description: Optional[str] = None
    creator_id: str
    visibility: VisibilityLevel = VisibilityLevel.PRIVATE
    items: List[ReadingListItem] = []
    tags: List[str] = []
    category: Optional[str] = None
    shared_with: List[SharedWith] = []


class ReadingListCreate(ReadingListBase):
    pass


class ReadingListUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[VisibilityLevel] = None
    items: Optional[List[ReadingListItem]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    shared_with: Optional[List[SharedWith]] = None


class ReadingListInDB(ReadingListBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ReadingListResponse(ReadingListBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class FeaturedContentType(str, Enum):
    EDITORS_PICK = "Editor's Pick"
    TRENDING = "Trending"
    NEW_ADDITION = "New Addition"


class FeaturedItem(BaseModel):
    video_id: str
    featured_reason: str
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None


class FeaturedContentBase(BaseModel):
    type: FeaturedContentType
    title: str
    description: str
    content: List[FeaturedItem] = []
    target_audience: List[str] = []
    categories: List[str] = []
    active: bool = True


class FeaturedContentCreate(FeaturedContentBase):
    pass


class FeaturedContentUpdate(BaseModel):
    type: Optional[FeaturedContentType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[List[FeaturedItem]] = None
    target_audience: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    active: Optional[bool] = None


class FeaturedContentInDB(FeaturedContentBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class FeaturedContentResponse(FeaturedContentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }