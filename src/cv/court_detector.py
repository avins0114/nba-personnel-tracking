"""Court detection and homography transformation."""

from typing import List, Tuple, Optional
import numpy as np
import cv2


class CourtDetector:
    """
    Detects court boundaries and computes homography transformation.

    For proof-of-concept, uses manual keypoint selection.
    Production version would use deep learning-based court detection.
    """

    def __init__(self):
        """Initialize court detector."""
        self.homography_matrix: Optional[np.ndarray] = None
        self.court_points_pixel: Optional[List[Tuple[int, int]]] = None
        self.court_points_real: Optional[List[Tuple[float, float]]] = None

        # NBA court dimensions in feet
        self.COURT_WIDTH = 50.0
        self.COURT_LENGTH = 94.0

    def set_manual_keypoints(
        self,
        pixel_points: List[Tuple[int, int]],
        real_points: Optional[List[Tuple[float, float]]] = None
    ):
        """
        Manually set court keypoints for homography.

        Args:
            pixel_points: List of (x, y) pixel coordinates in image
            real_points: List of (x, y) coordinates in feet on court
                        If None, uses default court corners
        """
        self.court_points_pixel = pixel_points

        if real_points is None:
            # Default: use 4 court corners
            # Court origin is baseline-left, x goes length-wise, y goes width-wise
            self.court_points_real = [
                (0.0, 0.0),           # Baseline left corner
                (94.0, 0.0),          # Baseline right corner (far end)
                (94.0, 50.0),         # Far right corner
                (0.0, 50.0)           # Near right corner
            ]
        else:
            self.court_points_real = real_points

        # Compute homography
        self._compute_homography()

    def _compute_homography(self):
        """Compute homography matrix from pixel to court coordinates."""
        if self.court_points_pixel is None or self.court_points_real is None:
            raise ValueError("Court points not set")

        if len(self.court_points_pixel) < 4:
            raise ValueError("Need at least 4 point correspondences")

        src_pts = np.array(self.court_points_pixel, dtype=np.float32)
        dst_pts = np.array(self.court_points_real, dtype=np.float32)

        self.homography_matrix, _ = cv2.findHomography(src_pts, dst_pts)
        print(f"Homography computed from {len(src_pts)} points")

    def detect_court_auto(self, frame: np.ndarray) -> bool:
        """
        Automatically detect court keypoints (placeholder for future implementation).

        Args:
            frame: Video frame

        Returns:
            True if court detected successfully
        """
        # TODO: Implement automatic court line detection
        # Approaches:
        # 1. Edge detection + Hough line transform
        # 2. Deep learning-based keypoint detection
        # 3. Template matching with known court patterns

        print("Automatic court detection not yet implemented. Use set_manual_keypoints().")
        return False

    def pixel_to_court(self, pixel_points: np.ndarray) -> np.ndarray:
        """
        Transform pixel coordinates to court coordinates.

        Args:
            pixel_points: Nx2 array of (x, y) pixel coordinates

        Returns:
            Nx2 array of (x, y) court coordinates in feet
        """
        if self.homography_matrix is None:
            raise ValueError("Homography not computed. Call set_manual_keypoints() first.")

        # Reshape for cv2.perspectiveTransform (needs shape [N, 1, 2])
        points = pixel_points.reshape(-1, 1, 2).astype(np.float32)
        transformed = cv2.perspectiveTransform(points, self.homography_matrix)
        return transformed.reshape(-1, 2)

    def court_to_pixel(self, court_points: np.ndarray) -> np.ndarray:
        """
        Transform court coordinates to pixel coordinates.

        Args:
            court_points: Nx2 array of (x, y) court coordinates in feet

        Returns:
            Nx2 array of (x, y) pixel coordinates
        """
        if self.homography_matrix is None:
            raise ValueError("Homography not computed")

        # Inverse homography
        inv_homography = np.linalg.inv(self.homography_matrix)
        points = court_points.reshape(-1, 1, 2).astype(np.float32)
        transformed = cv2.perspectiveTransform(points, inv_homography)
        return transformed.reshape(-1, 2)

    def interactive_keypoint_selection(self, frame: np.ndarray) -> bool:
        """
        Interactive GUI for selecting court keypoints.

        Args:
            frame: Video frame to display

        Returns:
            True if keypoints were successfully selected
        """
        points = []

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                cv2.circle(display_frame, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(
                    display_frame,
                    str(len(points)),
                    (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
                cv2.imshow('Select Court Keypoints', display_frame)

        display_frame = frame.copy()
        cv2.namedWindow('Select Court Keypoints')
        cv2.setMouseCallback('Select Court Keypoints', mouse_callback)

        instructions = [
            "Click 4 court corner points in order:",
            "1. Near-left baseline corner",
            "2. Far-left baseline corner",
            "3. Far-right baseline corner",
            "4. Near-right baseline corner",
            "Press ENTER when done, ESC to cancel"
        ]

        y_offset = 30
        for instruction in instructions:
            cv2.putText(
                display_frame,
                instruction,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )
            y_offset += 25

        cv2.imshow('Select Court Keypoints', display_frame)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 13 and len(points) >= 4:  # ENTER
                break
            elif key == 27:  # ESC
                cv2.destroyAllWindows()
                return False

        cv2.destroyAllWindows()

        if len(points) >= 4:
            self.set_manual_keypoints(points[:4])
            return True

        return False
