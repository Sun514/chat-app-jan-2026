# api/routers/media.py
"""
FastAPI router for splitting audio and video files.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.media import (
    MediaSplitService,
    SUPPORTED_EXTENSIONS,
    AUDIO_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])


class SupportedMediaTypesResponse(BaseModel):
    extensions: list[str]
    audio_extensions: list[str]
    video_extensions: list[str]
    count: int


class SplitResponse(BaseModel):
    success: bool
    filename: str
    chunk_count: int
    chunks: list[dict]
    message: str


class MediaInfoResponse(BaseModel):
    filename: str
    format: str
    duration_seconds: float
    file_size_mb: float
    is_audio: bool
    is_video: bool


async def get_media_service() -> MediaSplitService:
    """Get media split service instance."""
    return MediaSplitService()


@router.get("/supported-types", response_model=SupportedMediaTypesResponse)
async def get_supported_types():
    """Get list of supported audio and video file types."""
    return SupportedMediaTypesResponse(
        extensions=sorted(SUPPORTED_EXTENSIONS),
        audio_extensions=sorted(AUDIO_EXTENSIONS),
        video_extensions=sorted(VIDEO_EXTENSIONS),
        count=len(SUPPORTED_EXTENSIONS),
    )


@router.get("/info", response_model=MediaInfoResponse)
async def get_media_info(
    file: UploadFile = File(...),
    service: MediaSplitService = Depends(get_media_service),
):
    """
    Get information about an uploaded media file.

    Returns duration, format, and type (audio/video) info.
    """
    if not service.is_supported(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    try:
        content = await file.read()
        from io import BytesIO

        file_obj = BytesIO(content)
        file_obj.seek(0)

        duration, file_size_mb = service.get_duration_and_size(file_obj)
        ext = service.get_format(file.filename)

        return MediaInfoResponse(
            filename=file.filename,
            format=ext,
            duration_seconds=duration,
            file_size_mb=file_size_mb,
            is_audio=ext in AUDIO_EXTENSIONS,
            is_video=ext in VIDEO_EXTENSIONS,
        )
    except Exception as e:
        logger.error(f"Error getting media info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/split", response_model=SplitResponse)
async def split_media(
    file: UploadFile = File(...),
    chunk_duration: int = Form(
        default=None, ge=10, le=3600, description="Duration of each chunk in seconds"
    ),
    chunk_size_mb: int = Form(
        default=None, ge=1, le=2000, description="Size of each chunk in MB"
    ),
    service: MediaSplitService = Depends(get_media_service),
):
    """
    Split an audio or video file into smaller chunks.

    The file is split by duration or by file size. Original format is preserved.
    Users can download all split files.

    Args:
        file: Audio or video file to split
        chunk_duration: Duration of each chunk in seconds (10-3600)
        chunk_size_mb: Size of each chunk in MB (1-2000)

    Returns:
        Information about the split operation and list of chunk files
    """
    if not service.is_supported(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    if not chunk_duration and not chunk_size_mb:
        chunk_duration = 300

    if chunk_duration and chunk_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specify either chunk_duration or chunk_size_mb, not both",
        )

    try:
        content = await file.read()
        from io import BytesIO

        file_obj = BytesIO(content)
        file_obj.seek(0)

        chunks = service.split_file(
            file_obj,
            file.filename,
            chunk_duration=chunk_duration,
            chunk_size_mb=chunk_size_mb,
        )

        return SplitResponse(
            success=True,
            filename=file.filename,
            chunk_count=len(chunks),
            chunks=[
                {"filename": chunk_filename, "path": output_path}
                for output_path, chunk_filename in chunks
            ],
            message=f"Successfully split into {len(chunks)} chunks",
        )

    except Exception as e:
        logger.error(f"Error splitting media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/download/{chunk_filename}")
async def download_chunk(
    chunk_filename: str,
    service: MediaSplitService = Depends(get_media_service),
):
    """
    Download a specific split chunk file.

    Args:
        chunk_filename: Name of the chunk file to download

    Returns:
        The file for download
    """
    temp_dir = service.temp_dir
    file_path = os.path.join(temp_dir, chunk_filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk file not found. It may have been cleaned up or never created.",
        )

    return FileResponse(
        path=file_path,
        filename=chunk_filename,
        media_type="application/octet-stream",
    )
