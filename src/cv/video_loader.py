"""Video loading and frame extraction utilities."""

import cv2
from typing import Optional, Iterator, Tuple
import numpy as np


class VideoLoader:
    """Handles loading and frame extraction from video files."""

    def __init__(self, video_path: str):
        """
        Initialize video loader.

        Args:
            video_path: Path to video file
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Video loaded: {self.width}x{self.height} @ {self.fps} FPS, {self.total_frames} frames")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()

    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """
        Get a specific frame by number.

        Args:
            frame_number: Frame index to retrieve

        Returns:
            Frame as numpy array (BGR format) or None if frame not available
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        return frame if ret else None

    def frames(self, start_frame: int = 0, end_frame: Optional[int] = None) -> Iterator[Tuple[int, np.ndarray]]:
        """
        Iterate through frames.

        Args:
            start_frame: Starting frame index
            end_frame: Ending frame index (None for end of video)

        Yields:
            Tuple of (frame_number, frame_array)
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_number = start_frame
        end = end_frame if end_frame is not None else self.total_frames

        while frame_number < end:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame_number, frame
            frame_number += 1

    def get_timestamp(self, frame_number: int) -> float:
        """
        Get timestamp in seconds for a frame.

        Args:
            frame_number: Frame index

        Returns:
            Timestamp in seconds
        """
        return frame_number / self.fps if self.fps > 0 else 0.0
