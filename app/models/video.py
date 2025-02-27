from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    TUTORIAL = "Tutorial"
    DOCUMENTATION = "Documentation"
    CASE_STUDY = "Case Study"
    LECTURE = "Lecture"
    REVIEW = "Review"


class DifficultyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class Status(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    UNDER_REVIEW = "Under Review"


class ExpertiseLevel(str, Enum):
    BEGINNER_FRIENDLY = "Beginner-Friendly"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class ExerciseType(str, Enum):
    QUIZ = "Quiz"
    PRACTICE = "Practice"
    DISCUSSION = "Discussion"


class ResourceType(str, Enum):
    LINK = "Link"
    CODE = "Code"
    REFERENCE = "Reference"


class DifficultyRating(str, Enum):
    TOO_EASY = "Too Easy"
    JUST_RIGHT = "Just Right"
    TOO_HARD = "Too Hard"


class IssueType(str, Enum):
    CONTENT_ERROR = "Content Error"
    OUTDATED = "Outdated"
    UNCLEAR = "Unclear"


class IssueStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    RESOLVED = "Resolved"


class Thumbnails(BaseModel):
    default: HttpUrl
    high: HttpUrl


class Channel(BaseModel):
    id: str
    name: str
    url: HttpUrl
    expertise_level: Optional[ExpertiseLevel] = None
    content_quality: Optional[int] = Field(None, ge=1, le=10)


class Series(BaseModel):
    name: str
    order: int
    total_parts: int


class Exercise(BaseModel):
    type: ExerciseType
    content: str
    solution: Optional[str] = None


class Resource(BaseModel):
    type: ResourceType
    url: HttpUrl
    description: str


class GlossaryItem(BaseModel):
    term: str
    definition: str


class Chapter(BaseModel):
    title: str
    content: str
    timestamp: str
    key_points: List[str] = []
    exercises: List[Exercise] = []
    resources: List[Resource] = []


class DifficultyRatingItem(BaseModel):
    user_id: str
    rating: DifficultyRating
    feedback: Optional[str] = None


class UserRating(BaseModel):
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = None
    helpful_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReportedIssue(BaseModel):
    type: IssueType
    description: str
    status: IssueStatus = IssueStatus.OPEN
    reported_at: datetime = Field(default_factory=datetime.utcnow)


class UpdateHistory(BaseModel):
    date: datetime
    changes: str
    updated_by: str


class Metadata(BaseModel):
    description: str
    duration: int  # in seconds
    published_at: datetime
    thumbnails: Thumbnails
    language: Optional[str] = None
    subtitles: List[str] = []
    prerequisites: List[str] = []
    learning_outcomes: List[str] = []
    estimated_reading_time: Optional[int] = None  # in minutes


class LibraryData(BaseModel):
    categories: List[str] = []
    tags: List[str] = []
    difficulty: DifficultyLevel
    type: str
    primary_category: Optional[str] = None
    series: Optional[Series] = None
    content_structure: ContentType
    certification_track: Optional[str] = None
    skills_covered: List[str] = []


class Content(BaseModel):
    summary: str
    chapters: List[Chapter] = []
    transcript: Optional[str] = None
    glossary: List[GlossaryItem] = []
    key_takeaways: List[str] = []


class Engagement(BaseModel):
    views: int = 0
    completions: int = 0
    average_completion_time: Optional[int] = None
    difficulty_ratings: List[DifficultyRatingItem] = []
    user_ratings: List[UserRating] = []
    average_rating: Optional[float] = None
    reported_issues: List[ReportedIssue] = []


class Recommendations(BaseModel):
    next_reads: List[str] = []
    prerequisites: List[str] = []
    related_content: List[str] = []


class VideoBase(BaseModel):
    video_id: str
    title: str
    slug: str
    channel: Channel
    metadata: Metadata
    library_data: LibraryData
    content: Content
    engagement: Engagement = Field(default_factory=Engagement)
    recommendations: Recommendations = Field(default_factory=Recommendations)
    status: Status = Status.DRAFT
    last_verified: Optional[datetime] = None
    update_history: List[UpdateHistory] = []


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    channel: Optional[Channel] = None
    metadata: Optional[Metadata] = None
    library_data: Optional[LibraryData] = None
    content: Optional[Content] = None
    engagement: Optional[Engagement] = None
    recommendations: Optional[Recommendations] = None
    status: Optional[Status] = None
    last_verified: Optional[datetime] = None
    update_history: Optional[List[UpdateHistory]] = None


class VideoInDB(VideoBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class VideoResponse(VideoBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }