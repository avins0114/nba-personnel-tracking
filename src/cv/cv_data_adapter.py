"""Adapter to convert CV tracking data to SportVU-compatible format."""

from typing import List, Tuple, Optional
import numpy as np
from ..moment import Moment
from ..player import Player
from ..ball import Ball
from .video_loader import VideoLoader
from .player_detector import PlayerDetector
from .player_tracker import PlayerTracker
from .court_detector import CourtDetector
from .manual_selector import ManualPlayerSelector


class CVDataAdapter:
    """
    Converts computer vision tracking data to SportVU-compatible Moment objects.

    This allows CV-tracked data to use the same visualization and analysis code
    as SportVU data.
    """

    def __init__(
        self,
        video_path: str,
        court_detector: Optional[CourtDetector] = None,
        half_court: bool = False
    ):
        """
        Initialize CV data adapter.

        Args:
            video_path: Path to video file
            court_detector: CourtDetector with calibrated homography
            half_court: Whether video shows only half court (typical broadcast)
        """
        self.video_loader = VideoLoader(video_path)
        self.detector = PlayerDetector(model_name='yolov8n.pt', confidence_threshold=0.5)
        self.tracker = PlayerTracker(max_age=30)
        self.court_detector = court_detector
        self.half_court = half_court

        # Team IDs (arbitrary for CV data)
        self.HOME_TEAM_ID = 1610612744  # GSW team ID (arbitrary choice)
        self.AWAY_TEAM_ID = 1610612739  # CLE team ID (arbitrary choice)

        # Store video frames for visualization
        self.video_frames = []

    def process_video(
        self,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        max_frames: Optional[int] = None,
        store_frames: bool = False
    ) -> List[Moment]:
        """
        Process video and extract moments.

        Args:
            start_frame: Starting frame number
            end_frame: Ending frame number (None for end of video)
            max_frames: Maximum number of frames to process
            store_frames: Whether to store original video frames for visualization

        Returns:
            List of Moment objects
        """
        moments = []
        frame_count = 0

        if end_frame is None and max_frames is not None:
            end_frame = start_frame + max_frames

        print(f"Processing video frames {start_frame} to {end_frame or 'end'}...")

        # Clear previous frames
        if store_frames:
            self.video_frames = []

        for frame_num, frame in self.video_loader.frames(start_frame, end_frame):
            if max_frames is not None and frame_count >= max_frames:
                break

            # Detect players
            detections = self.detector.detect(frame)

            # Track players
            tracked = self.tracker.update(frame, detections)

            # Convert to Moment
            moment = self._create_moment(frame_num, tracked, frame)
            if moment is not None:
                moments.append(moment)
                # Store frame for visualization
                if store_frames:
                    self.video_frames.append(frame.copy())

            frame_count += 1

            if frame_count % 25 == 0:  # Progress every second (at 25 FPS)
                print(f"Processed {frame_count} frames, {len(moments)} moments created")

        print(f"Finished: {len(moments)} moments from {frame_count} frames")
        return moments

    def process_video_with_manual_selection(
        self,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        max_frames: Optional[int] = None,
        store_frames: bool = False
    ) -> List[Moment]:
        """
        Process video with manual player selection in first frame.

        Args:
            start_frame: Starting frame number
            end_frame: Ending frame number (None for end of video)
            max_frames: Maximum number of frames to process
            store_frames: Whether to store original video frames for visualization

        Returns:
            List of Moment objects
        """
        # Get first frame for manual selection
        first_frame = self.video_loader.get_frame(start_frame)
        if first_frame is None:
            print(f"Could not load frame {start_frame}")
            return []

        # Manual selection interface
        selector = ManualPlayerSelector(first_frame)
        selections = selector.select_players()

        if selections is None:
            print("Manual selection cancelled.")
            return []

        # Get initial detections and team assignments
        initial_detections = selector.get_detections_for_tracker()
        team_assignments = selector.get_team_assignments()
        ball_bbox = selector.get_ball_bbox()

        print(f"\n{len(initial_detections)} players selected, starting tracking...")

        moments = []
        frame_count = 0

        if end_frame is None and max_frames is not None:
            end_frame = start_frame + max_frames

        print(f"Processing video frames {start_frame} to {end_frame or 'end'}...")

        # Clear previous frames
        if store_frames:
            self.video_frames = []

        # Initialize tracker with manual selections
        first_tracked = self.tracker.update(first_frame, initial_detections)

        # Override team assignments with manual selections
        for i, (x1, y1, x2, y2, track_id, _) in enumerate(first_tracked):
            if i in team_assignments:
                self.tracker.team_assignments[track_id] = team_assignments[i]

        # Create first moment
        moment = self._create_moment(start_frame, first_tracked, first_frame, ball_bbox)
        if moment is not None:
            moments.append(moment)
            if store_frames:
                self.video_frames.append(first_frame.copy())

        frame_count += 1

        # Process remaining frames
        for frame_num, frame in self.video_loader.frames(start_frame + 1, end_frame):
            if max_frames is not None and frame_count >= max_frames:
                break

            # Detect players
            detections = self.detector.detect(frame)

            # Track players
            tracked = self.tracker.update(frame, detections)

            # Convert to Moment
            moment = self._create_moment(frame_num, tracked, frame, ball_bbox)
            if moment is not None:
                moments.append(moment)
                if store_frames:
                    self.video_frames.append(frame.copy())

            frame_count += 1

            if frame_count % 25 == 0:
                print(f"Processed {frame_count} frames, {len(moments)} moments created")

        print(f"Finished: {len(moments)} moments from {frame_count} frames")
        return moments

    def _create_moment(
        self,
        frame_num: int,
        tracked_players: List[Tuple[int, int, int, int, int, str]],
        frame: np.ndarray,
        ball_bbox: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[Moment]:
        """
        Create a Moment from tracked players.

        Args:
            frame_num: Frame number
            tracked_players: List of (x1, y1, x2, y2, track_id, team)
            frame: Video frame
            ball_bbox: Optional ball bounding box (x1, y1, x2, y2)

        Returns:
            Moment object or None if insufficient data
        """
        # Need at least some players to create a moment
        if len(tracked_players) == 0:
            return None

        # Simplified time tracking - just use frame count
        # CV tracking doesn't have real game clock information
        quarter = 1  # Default to Q1 for CV data
        game_clock = 600.0  # Fixed time for all CV frames (10 minutes)

        # Convert player positions to court coordinates
        players = []
        for x1, y1, x2, y2, track_id, team in tracked_players:
            # Use foot position (bottom-center of bbox)
            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)

            # Transform to court coordinates if homography available
            if self.court_detector is not None and self.court_detector.homography_matrix is not None:
                pixel_point = np.array([[foot_x, foot_y]], dtype=np.float32)
                court_point = self.court_detector.pixel_to_court(pixel_point)[0]
                court_x, court_y = float(court_point[0]), float(court_point[1])
            else:
                # Fallback: simple linear mapping (very approximate!)
                frame_height, frame_width = frame.shape[:2]
                if self.half_court:
                    # Map to half court (0-47 feet)
                    court_x = (foot_x / frame_width) * 47.0
                else:
                    # Map to full court (0-94 feet)
                    court_x = (foot_x / frame_width) * 94.0
                court_y = (foot_y / frame_height) * 50.0

            # Determine team ID
            team_id = self.HOME_TEAM_ID if team == 'home' else self.AWAY_TEAM_ID

            player = Player(
                team_id=team_id,
                player_id=track_id,  # Use track ID as player ID
                x=court_x,
                y=court_y,
                firstname=f"Player",
                lastname=f"{track_id}",
                jersey=str(track_id),
                position=None
            )
            players.append(player)

        # Create ball
        if ball_bbox is not None:
            # Use manually selected ball position
            x1, y1, x2, y2 = ball_bbox
            ball_foot_x = int((x1 + x2) / 2)
            ball_foot_y = int(y2)

            # Transform to court coordinates
            if self.court_detector is not None and self.court_detector.homography_matrix is not None:
                pixel_point = np.array([[ball_foot_x, ball_foot_y]], dtype=np.float32)
                court_point = self.court_detector.pixel_to_court(pixel_point)[0]
                ball_x, ball_y = float(court_point[0]), float(court_point[1])
            else:
                # Fallback: simple linear mapping
                frame_height, frame_width = frame.shape[:2]
                if self.half_court:
                    ball_x = (ball_foot_x / frame_width) * 47.0
                else:
                    ball_x = (ball_foot_x / frame_width) * 94.0
                ball_y = (ball_foot_y / frame_height) * 50.0

            ball = Ball(x=ball_x, y=ball_y, radius=5.0)
        else:
            # Dummy ball at center court (or half court center)
            if self.half_court:
                ball = Ball(x=23.5, y=25.0, radius=5.0)  # Half court center
            else:
                ball = Ball(x=47.0, y=25.0, radius=5.0)  # Full court center

        # Create moment
        moment = Moment(
            quarter=quarter,
            game_clock=game_clock,
            shot_clock=None,
            ball=ball,
            players=players,
            home_team_id=self.HOME_TEAM_ID,
            away_team_id=self.AWAY_TEAM_ID
        )

        return moment

    def setup_court_calibration(self, frame_num: int = 0) -> bool:
        """
        Interactive setup of court calibration.

        Args:
            frame_num: Frame to use for calibration

        Returns:
            True if calibration successful
        """
        frame = self.video_loader.get_frame(frame_num)
        if frame is None:
            print(f"Could not load frame {frame_num}")
            return False

        if self.court_detector is None:
            self.court_detector = CourtDetector()

        return self.court_detector.interactive_keypoint_selection(frame)

    def close(self):
        """Release resources."""
        self.video_loader.close()
