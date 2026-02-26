"""Service for splitting audio/video files into smaller parts."""

import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)

SPLITS_DIR = Path("/tmp/media_splits")


@dataclass
class PartInfo:
    filename: str
    size_bytes: int
    duration_seconds: float


class MediaSplitterService:
    """Splits media files by duration or size using ffmpeg."""

    def _get_duration_seconds(self, file_path: str) -> float:
        """Get media duration using ffprobe."""
        probe = ffmpeg.probe(file_path)
        return float(probe["format"]["duration"])

    def _make_output_dir(self) -> tuple[str, Path]:
        job_id = str(uuid.uuid4())
        output_dir = SPLITS_DIR / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return job_id, output_dir

    def _part_filename(self, original: str, index: int) -> str:
        stem = Path(original).stem
        ext = Path(original).suffix
        return f"{stem}_{index + 1:03d}{ext}"

    def _split_by_segment_secs(
        self, file_path: str, segment_secs: float, original_name: str, output_dir: Path,
    ) -> list[PartInfo]:
        total_duration = self._get_duration_seconds(file_path)
        parts: list[PartInfo] = []

        i = 0
        start = 0.0
        while start < total_duration:
            part_name = self._part_filename(original_name, i)
            out_path = output_dir / part_name

            (
                ffmpeg
                .input(file_path, ss=start, t=segment_secs)
                .output(str(out_path), c="copy")
                .overwrite_output()
                .run(quiet=True)
            )

            actual_duration = min(segment_secs, total_duration - start)
            # Get precise duration from the output file
            try:
                out_probe = ffmpeg.probe(str(out_path))
                actual_duration = float(out_probe["format"]["duration"])
            except Exception:
                pass

            parts.append(PartInfo(
                filename=part_name,
                size_bytes=os.path.getsize(out_path),
                duration_seconds=round(actual_duration, 2),
            ))

            start += segment_secs
            i += 1

        logger.info(f"Split into {len(parts)} parts in {output_dir}")
        return parts

    def split_by_duration(
        self, file_path: str, segment_minutes: float, original_filename: str | None = None,
    ) -> tuple[str, list[PartInfo]]:
        """Split file into segments of N minutes each."""
        job_id, output_dir = self._make_output_dir()
        original_name = original_filename or Path(file_path).name
        segment_secs = segment_minutes * 60
        parts = self._split_by_segment_secs(file_path, segment_secs, original_name, output_dir)
        return job_id, parts

    def extract_audio(
        self, file_path: str, output_format: str = "mp3", original_filename: str | None = None,
    ) -> tuple[str, PartInfo]:
        """Extract audio track from a media file."""
        job_id, output_dir = self._make_output_dir()
        original_name = original_filename or Path(file_path).name
        stem = Path(original_name).stem
        out_name = f"{stem}.{output_format}"
        out_path = output_dir / out_name

        (
            ffmpeg
            .input(file_path)
            .output(str(out_path), vn=None)
            .overwrite_output()
            .run(quiet=True)
        )

        duration = 0.0
        try:
            out_probe = ffmpeg.probe(str(out_path))
            duration = float(out_probe["format"]["duration"])
        except Exception:
            pass

        part = PartInfo(
            filename=out_name,
            size_bytes=os.path.getsize(out_path),
            duration_seconds=round(duration, 2),
        )
        logger.info(f"Extracted audio to {out_path}")
        return job_id, part

    def split_by_size(
        self, file_path: str, target_size_mb: float, original_filename: str | None = None,
    ) -> tuple[str, list[PartInfo]]:
        """Split file into segments targeting N MB each."""
        job_id, output_dir = self._make_output_dir()
        original_name = original_filename or Path(file_path).name
        file_size = os.path.getsize(file_path)
        total_duration = self._get_duration_seconds(file_path)

        # Estimate segment duration from bitrate
        bitrate = file_size / total_duration  # bytes per second
        target_bytes = target_size_mb * 1024 * 1024
        segment_secs = target_bytes / bitrate

        parts = self._split_by_segment_secs(file_path, segment_secs, original_name, output_dir)
        return job_id, parts
