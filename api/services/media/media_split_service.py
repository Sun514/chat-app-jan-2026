import os
import tempfile
import logging
from pathlib import Path
from typing import BinaryIO, List, Tuple

import ffmpeg

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {"mp3", "wav", "aac", "m4a", "ogg", "flac", "wma", "aiff"}

VIDEO_EXTENSIONS = {
    "mp4",
    "avi",
    "mkv",
    "mov",
    "wmv",
    "flv",
    "webm",
    "m4v",
    "mpeg",
    "mpg",
}

SUPPORTED_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


class MediaSplitService:
    """Service for splitting audio and video files into smaller chunks."""

    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported."""
        ext = Path(filename).suffix.lstrip(".").lower()
        return ext in SUPPORTED_EXTENSIONS

    def get_format(self, filename: str) -> str:
        """Get the file format/extension."""
        return Path(filename).suffix.lstrip(".").lower()

    def get_duration(self, file: BinaryIO) -> float:
        """Get the duration of the media file in seconds."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            probe = ffmpeg.probe(tmp_path)
            duration = float(probe["format"]["duration"])
            return duration
        except Exception as e:
            logger.error(f"Error probing media file: {e}")
            raise ValueError(f"Could not determine media duration: {e}")
        finally:
            os.unlink(tmp_path)

    def get_duration_and_size(self, file: BinaryIO) -> tuple:
        """Get the duration and size of the media file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            probe = ffmpeg.probe(tmp_path)
            duration = float(probe["format"]["duration"])
            file_size_mb = float(probe["format"]["size"]) / (1024 * 1024)
            return duration, file_size_mb
        except Exception as e:
            logger.error(f"Error probing media file: {e}")
            raise ValueError(f"Could not determine media info: {e}")
        finally:
            os.unlink(tmp_path)

    def split_file(
        self,
        file: BinaryIO,
        filename: str,
        chunk_duration: int = None,
        chunk_size_mb: int = None,
    ) -> List[Tuple[str, str]]:
        """
        Split media file into smaller chunks.

        Args:
            file: The uploaded file object
            filename: Original filename
            chunk_duration: Duration of each chunk in seconds
            chunk_size_mb: Size of each chunk in megabytes

        Returns:
            List of tuples (output_path, chunk_filename)
        """
        if not self.is_supported(filename):
            raise ValueError(f"Unsupported file type: {filename}")

        if not chunk_duration and not chunk_size_mb:
            chunk_duration = 300

        ext = self.get_format(filename)
        base_name = Path(filename).stem

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            probe = ffmpeg.probe(tmp_path)
            total_duration = float(probe["format"]["duration"])
            total_size_mb = float(probe["format"]["size"]) / (1024 * 1024)

            chunk_paths = []

            if chunk_size_mb:
                num_chunks = int((total_size_mb + chunk_size_mb - 1) // chunk_size_mb)
                estimated_duration_per_chunk = total_duration / num_chunks
                chunk_duration = max(1, int(estimated_duration_per_chunk))

            num_chunks = int((total_duration + chunk_duration - 1) // chunk_duration)

            for i in range(num_chunks):
                start_time = i * chunk_duration
                output_filename = f"{base_name}_part{i + 1:03d}.{ext}"
                output_path = os.path.join(self.temp_dir, output_filename)

                stream = ffmpeg.input(tmp_path, ss=start_time)
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    t=chunk_duration,
                    c="copy",
                    y=None,
                )
                ffmpeg.run(stream, overwrite_output=True, quiet=True)

                chunk_paths.append((output_path, output_filename))
                logger.info(f"Created chunk: {output_filename}")

            return chunk_paths

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise ValueError(f"Error splitting media file: {e}")
        except Exception as e:
            logger.error(f"Error splitting media: {e}")
            raise
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
