"""Player detection using YOLO object detection."""

from typing import List, Tuple
import numpy as np


class PlayerDetector:
    """Detects players in video frames using YOLO."""

    def __init__(self, model_name: str = 'yolov8n.pt', confidence_threshold: float = 0.5):
        """
        Initialize player detector.

        Args:
            model_name: YOLO model to use (yolov8n.pt is fastest, yolov8x.pt is most accurate)
            confidence_threshold: Minimum confidence for detections
        """
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_name)
            self.confidence_threshold = confidence_threshold
            print(f"Loaded YOLO model: {model_name}")
        except ImportError:
            raise ImportError(
                "ultralytics package not installed. "
                "Install with: pip install ultralytics"
            )

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect players in a frame.

        Args:
            frame: Video frame (BGR format from OpenCV)

        Returns:
            List of detections as (x1, y1, x2, y2, confidence)
            where (x1, y1) is top-left and (x2, y2) is bottom-right
        """
        # Run YOLO detection - class 0 is 'person'
        results = self.model(frame, classes=[0], verbose=False)

        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes.data.cpu().numpy()

            for box in boxes:
                x1, y1, x2, y2, conf, cls = box
                if conf >= self.confidence_threshold:
                    # Filter out non-players using heuristics
                    if self._is_likely_player(frame, x1, y1, x2, y2):
                        detections.append((int(x1), int(y1), int(x2), int(y2), float(conf)))

        return detections

    def _is_likely_player(self, frame: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> bool:
        """
        Filter detections to only include likely players (not refs, coaches, fans).

        Args:
            frame: Video frame
            x1, y1, x2, y2: Bounding box coordinates

        Returns:
            True if detection is likely a player
        """
        width = x2 - x1
        height = y2 - y1

        # Basic size filtering
        # Players should be reasonably sized (not too small = fans, not too large = coaches)
        frame_height = frame.shape[0]
        frame_width = frame.shape[1]

        relative_height = height / frame_height
        aspect_ratio = height / width if width > 0 else 0

        # Heuristics (these are approximate and may need tuning):
        # - Players are at least 10% of frame height
        # - Players have aspect ratio roughly 2:1 to 3:1 (taller than wide)
        # - Players are not in bottom 5% of frame (likely sideline/bench)

        if relative_height < 0.1 or relative_height > 0.8:
            return False

        if aspect_ratio < 1.5 or aspect_ratio > 4.0:
            return False

        # Filter out people at very top (unlikely to be on court)
        if y1 < frame_height * 0.05:
            return False

        return True

    def detect_with_positions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float, Tuple[int, int]]]:
        """
        Detect players and compute foot positions (for court mapping).

        Args:
            frame: Video frame

        Returns:
            List of (x1, y1, x2, y2, confidence, (foot_x, foot_y))
        """
        detections = self.detect(frame)
        detections_with_feet = []

        for x1, y1, x2, y2, conf in detections:
            # Estimate foot position as bottom-center of bounding box
            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)  # Bottom of bbox
            detections_with_feet.append((x1, y1, x2, y2, conf, (foot_x, foot_y)))

        return detections_with_feet
