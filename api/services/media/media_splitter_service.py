"""Service for splitting audio/video files into smaller parts."""

import logging
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SPLITS_DIR = Path("/tmp/media_splits")


@dataclass
class PartInfo:
    filename: str
    size_bytes: int
    duration_seconds: float


class MediaSplitterService:
    """Splits media files by duration or size."""

    def _is_audio(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in AUDIO_EXTENSIONS

    def _is_video(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in VIDEO_EXTENSIONS

    def _get_duration_seconds(self, file_path: str) -> float:
        """Get media duration using ffprobe."""
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-show_entries",
                "format=duration", "-of", "csv=p=0", file_path,
            ],
            capture_output=True, text=True,
        )
        return float(result.stdout.strip())

    def _make_output_dir(self) -> tuple[str, Path]:
        job_id = str(uuid.uuid4())
        output_dir = SPLITS_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return job_id, output_dir

    def _part_filename(self, original: str, index: int) -> str:
        stem = Path(original).stem
        ext = Path(original).suffix
        return f"{stem}_{index + 1:03d}{ext}"

    def split_by_duration(self, file_path: str, segment_minutes: float, original_filename: str | None = None) -> tuple[str, list[PartInfo]]:
        """Split file into segments of N minutes each."""
        job_id, output_dir = self._make_output_dir()
        segment_ms = int(segment_minutes * 60 * 1000)
        original_name = original_filename or Path(file_path).name

        if self._is_audio(file_path):
            return job_id, self._split_audio_by_duration(file_path, original_name, segment_ms, output_dir)
        else:
            segment_secs = segment_minutes * 60
            return job_id, self._split_video_by_duration(file_path, original_name, segment_secs, output_dir)

    def split_by_size(self, file_path: str, target_size_mb: float, original_filename: str | None = None) -> tuple[str, list[PartInfo]]:
        """Split file into segments targeting N MB each."""
        job_id, output_dir = self._make_output_dir()
        original_name = original_filename or Path(file_path).name
        file_size = os.path.getsize(file_path)
        total_duration = self._get_duration_seconds(file_path)

        # Estimate segment duration from bitrate
        bitrate = file_size / total_duration  # bytes per second
        target_bytes = target_size_mb * 1024 * 1024
        segment_secs = target_bytes / bitrate

        if self._is_audio(file_path):
            segment_ms = int(segment_secs * 1000)
            return job_id, self._split_audio_by_duration(file_path, original_name, segment_ms, output_dir)
        else:
            return job_id, self._split_video_by_duration(file_path, original_name, segment_secs, output_dir)

    def _split_audio_by_duration(
        self, file_path: str, original_name: str, segment_ms: int, output_dir: Path,
    ) -> list[PartInfo]:
        audio = AudioSegment.from_file(file_path)
        parts: list[PartInfo] = []

        for i, start in enumerate(range(0, len(audio), segment_ms)):
            segment = audio[start:start + segment_ms]
            part_name = self._part_filename(original_name, i)
            out_path = output_dir / part_name

            ext = Path(original_name).suffix.lstrip(".").lower()
            export_format = "ipod" if ext == "m4a" else ext
            segment.export(str(out_path), format=export_format)

            parts.append(PartInfo(
                filename=part_name,
                size_bytes=os.path.getsize(out_path),
                duration_seconds=len(segment) / 1000.0,
            ))

        logger.info(f"Split audio into {len(parts)} parts in {output_dir}")
        return parts

    def _split_video_by_duration(
        self, file_path: str, original_name: str, segment_secs: float, output_dir: Path,
    ) -> list[PartInfo]:
        total_duration = self._get_duration_seconds(file_path)
        parts: list[PartInfo] = []
        ext = Path(original_name).suffix

        i = 0
        start = 0.0
        while start < total_duration:
            part_name = self._part_filename(original_name, i)
            out_path = output_dir / part_name

            cmd = [
                "ffmpeg", "-y", "-i", file_path,
                "-ss", str(start), "-t", str(segment_secs),
                "-c", "copy", str(out_path),
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            duration = min(segment_secs, total_duration - start)
            parts.append(PartInfo(
                filename=part_name,
                size_bytes=os.path.getsize(out_path),
                duration_seconds=round(duration, 2),
            ))

            start += segment_secs
            i += 1

        logger.info(f"Split video into {len(parts)} parts in {output_dir}")
        return parts
