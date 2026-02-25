import os
import shutil
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, UploadFile, Query, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.media.splitter import split_media_file, create_zip_archive

router = APIRouter(prefix="/media", tags=["Media Processing"])

class SplitMethod(str, Enum):
    duration = "duration"
    size = "size"

class SplitResponse(BaseModel):
    session_id: str
    files: List[str]
    zip_url: str
    file_urls: List[str]

TEMP_BASE_DIR = tempfile.gettempdir()

@router.post("/split", response_model=SplitResponse)
async def split_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: SplitMethod = Query(..., description="Method to split: 'duration' (minutes) or 'size' (MB)"),
    value: float = Query(..., gt=0, description="Duration in minutes OR size in MB")
):
    """
    Splits an audio/video file into smaller segments based on duration or size.
    Returns session ID and URLs to download the generated files.
    """
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Filename required.")
        
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_BASE_DIR, f"media_split_{session_id}")
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        # Save uploaded file
        original_ext = Path(file.filename).suffix
        original_stem = Path(file.filename).stem
        input_file_path = os.path.join(session_dir, f"input_{original_stem}{original_ext}")
        
        with open(input_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Call splitter service
        output_dir = os.path.join(session_dir, "output")
        try:
            split_files = await split_media_file(
                file_path=input_file_path,
                output_dir=output_dir,
                split_method=method.value,
                split_value=value
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=f"Error splitting media: {str(e)}")
            
        if not split_files:
            raise HTTPException(status_code=500, detail="No segments were created.")
            
        # Create zip archive of the split files
        zip_filename = f"{original_stem}_splits.zip"
        zip_path = os.path.join(session_dir, zip_filename)
        create_zip_archive(split_files, zip_path)
        
        file_names = [Path(f).name for f in split_files]
        file_urls = [f"/media/download/{session_id}/{fn}" for fn in file_names]
        
        return SplitResponse(
            session_id=session_id,
            files=file_names,
            zip_url=f"/media/download/{session_id}/{zip_filename}",
            file_urls=file_urls
        )
        
    except Exception as e:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """
    Download a specific split file or the zip archive.
    """
    session_dir = os.path.join(TEMP_BASE_DIR, f"media_split_{session_id}")
    
    # Security check: prevent directory traversal
    safe_filename = os.path.basename(filename)
    
    # File could be in session_dir (the zip) or session_dir/output (the split files)
    zip_path = os.path.join(session_dir, safe_filename)
    split_path = os.path.join(session_dir, "output", safe_filename)
    
    if os.path.exists(zip_path):
        return FileResponse(path=zip_path, filename=safe_filename)
    elif os.path.exists(split_path):
        return FileResponse(path=split_path, filename=safe_filename)
    else:
        raise HTTPException(status_code=404, detail="File not found or expired")
