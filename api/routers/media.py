"""Media file splitting endpoints."""

import io
import logging
import os
import uuid
import zipfile
from enum import Enum
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from api.services.media.media_splitter_service import MediaSplitterService, SPLITS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media", tags=["media"])

UPLOADS_DIR = Path("/tmp/media_uploads")
splitter = MediaSplitterService()


class SplitBy(str, Enum):
    duration = "duration"
    size = "size"


@router.post("/split")
async def split_media(
    file: UploadFile = File(...),
    split_by: SplitBy = Form(...),
    value: float = Form(...),
):
    """Upload and split a media file by duration or size."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = uuid.uuid4()
    upload_path = UPLOADS_DIR / f"{upload_id}_{file.filename}"

    # Save uploaded file
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    original_size = os.path.getsize(upload_path)

    try:
        if split_by == SplitBy.duration:
            job_id, parts = splitter.split_by_duration(str(upload_path), value, original_filename=file.filename)
        else:
            job_id, parts = splitter.split_by_size(str(upload_path), value, original_filename=file.filename)
    except Exception as e:
        logger.error(f"Failed to split file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to split file: {e}")
    finally:
        # Clean up uploaded file
        upload_path.unlink(missing_ok=True)

    return {
        "job_id": job_id,
        "original_filename": file.filename,
        "original_size_bytes": original_size,
        "split_by": split_by.value,
        "value": value,
        "parts": [
            {
                "filename": p.filename,
                "size_bytes": p.size_bytes,
                "duration_seconds": p.duration_seconds,
                "download_url": f"/media/download/{job_id}/{p.filename}",
            }
            for p in parts
        ],
        "total_parts": len(parts),
    }


@router.get("/download/{job_id}/{filename}")
async def download_part(job_id: str, filename: str):
    """Download a split file part."""
    file_path = SPLITS_DIR / job_id / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path), filename=filename)


@router.get("/download-zip/{job_id}")
async def download_zip(job_id: str):
    """Download all split parts as a single zip file."""
    job_dir = SPLITS_DIR / job_id
    if not job_dir.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(job_dir.iterdir()):
            if f.is_file():
                zf.write(f, f.name)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={job_id}.zip"},
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """List available files for a split job."""
    job_dir = SPLITS_DIR / job_id
    if not job_dir.is_dir():
        raise HTTPException(status_code=404, detail="Job not found")

    parts = []
    for f in sorted(job_dir.iterdir()):
        if f.is_file():
            parts.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "download_url": f"/media/download/{job_id}/{f.name}",
            })

    return {
        "job_id": job_id,
        "parts": parts,
        "total_parts": len(parts),
    }
