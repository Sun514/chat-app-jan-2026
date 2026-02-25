import os
import subprocess
import shutil
import zipfile
import tempfile
import asyncio
from pathlib import Path
from typing import List

async def get_bitrate(file_path: str) -> float:
    """Get bitrate of media file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise ValueError(f"Failed to get bitrate: {stderr.decode()}")
        
    bitrate_str = stdout.decode().strip()
    if not bitrate_str or bitrate_str == "N/A":
        # Fallback to estimating via file size and duration
        return await estimate_bitrate(file_path)
    
    return float(bitrate_str)

async def estimate_bitrate(file_path: str) -> float:
    """Estimate bitrate via file size and duration."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise ValueError(f"Failed to get duration: {stderr.decode()}")
        
    duration_str = stdout.decode().strip()
    if not duration_str or duration_str == "N/A":
        raise ValueError("Could not determine media duration or bitrate.")
        
    duration = float(duration_str)
    size_bytes = os.path.getsize(file_path)
    
    # bitrate in bits per second: (size_bytes * 8) / duration
    if duration <= 0:
        raise ValueError("Media duration is zero or invalid.")
    return (size_bytes * 8.0) / duration

async def split_media_file(
    file_path: str,
    output_dir: str,
    split_method: str,
    split_value: float
) -> List[str]:
    """
    Splits media using ffmpeg.
    split_method: "duration" (value in minutes) or "size" (value in MB)
    Returns list of output file paths.
    """
    file_path_obj = Path(file_path)
    out_dir_obj = Path(output_dir)
    out_dir_obj.mkdir(parents=True, exist_ok=True)
    
    # Avoid % in string formatting conflict with Path
    output_pattern = out_dir_obj / f"{file_path_obj.stem}_%03d{file_path_obj.suffix}"
    
    segment_time = 0.0
    
    if split_method == "duration":
        # value is in minutes
        segment_time = split_value * 60.0
    elif split_method == "size":
        # value is in MB
        bitrate = await get_bitrate(str(file_path_obj))
        target_bits = split_value * 1024 * 1024 * 8
        if bitrate <= 0:
            raise ValueError("Invalid bitrate detected.")
        segment_time = target_bits / bitrate
        if segment_time <= 0:
            raise ValueError("Calculated segment time is invalid.")
    else:
        raise ValueError("Invalid split method. Use 'duration' or 'size'.")
        
    cmd = [
        "ffmpeg", "-y", "-i", str(file_path_obj),
        "-c", "copy", "-map", "0",
        "-segment_time", str(segment_time), "-f", "segment",
        "-reset_timestamps", "1",
        str(output_pattern)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg split failed: {stderr.decode()}")
        
    # Get created files, return sorted
    files = sorted(out_dir_obj.glob(f"{file_path_obj.stem}_*{file_path_obj.suffix}"))
    return [str(f) for f in files]

def create_zip_archive(file_paths: List[str], zip_path: str) -> str:
    """Creates a zip archive from a list of files."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            p = Path(file_path)
            zipf.write(file_path, arcname=p.name)
    return zip_path
