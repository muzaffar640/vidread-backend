from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
from app.services.video import VideoService
from pydantic import BaseModel, HttpUrl

router = APIRouter()
video_service = VideoService()


class VideoURLInput(BaseModel):
    url: HttpUrl


class VideoSearchParams(BaseModel):
    skip: int = 0
    limit: int = 10
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None


@router.post("/videos/process")
async def process_video(input_data: VideoURLInput):
    """
    Process a YouTube video URL to extract and enhance content.
    """
    try:
        processed_video = await video_service.process_and_save_video(str(input_data.url))
        return processed_video
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


@router.get("/videos")
async def get_videos(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    search: Optional[str] = None
):
    """
    Get videos with filtering options.
    """
    try:
        videos = await video_service.get_videos(skip, limit, category, tags, search)
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting videos: {str(e)}")


@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    Get a video by its ID.
    """
    try:
        video = await video_service.get_video_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video: {str(e)}")


@router.put("/videos/{video_id}")
async def update_video(video_id: str, update_data: dict = Body(...)):
    """
    Update a video document.
    """
    try:
        updated_video = await video_service.update_video(video_id, update_data)
        if not updated_video:
            raise HTTPException(status_code=404, detail="Video not found")
        return updated_video
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating video: {str(e)}")


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """
    Delete a video document.
    """
    try:
        deleted = await video_service.delete_video(video_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Video not found")
        return {"message": "Video deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting video: {str(e)}")