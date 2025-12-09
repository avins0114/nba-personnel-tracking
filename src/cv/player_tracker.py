"""Player tracking across frames using DeepSORT."""

from typing import List, Tuple, Optional
import numpy as np


class PlayerTracker:
    """Maintains consistent player IDs across video frames using DeepSORT."""

    def __init__(self, max_age: int = 30, n_init: int = 3):
        """
        Initialize tracker.

        Args:
            max_age: Maximum frames to keep track alive without detection
            n_init: Number of consecutive detections before track is confirmed
        """
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            self.tracker = DeepSort(
                max_age=max_age,
                n_init=n_init,
                nms_max_overlap=0.7,
                max_cosine_distance=0.3,
                nn_budget=100,
                embedder="mobilenet",
                embedder_gpu=False
            )
            print("DeepSORT tracker initialized")
        except ImportError:
            raise ImportError(
                "deep-sort-realtime package not installed. "
                "Install with: pip install deep-sort-realtime"
            )

        self.team_assignments = {}  # track_id -> team ('home' or 'away')

    def update(
        self,
        frame: np.ndarray,
        detections: List[Tuple[int, int, int, int, float]]
    ) -> List[Tuple[int, int, int, int, int, str]]:
        """
        Update tracker with new detections.

        Args:
            frame: Current video frame
            detections: List of (x1, y1, x2, y2, confidence)

        Returns:
            List of tracked players as (x1, y1, x2, y2, track_id, team)
        """
        # Convert detections to DeepSORT format
        # DeepSORT expects: ([left, top, width, height], confidence, class)
        ds_detections = []
        for x1, y1, x2, y2, conf in detections:
            left = x1
            top = y1
            width = x2 - x1
            height = y2 - y1
            ds_detections.append(([left, top, width, height], conf, 'person'))

        # Update tracker
        tracks = self.tracker.update_tracks(ds_detections, frame=frame)

        # Extract track information
        tracked_players = []
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()  # Get left, top, right, bottom
            x1, y1, x2, y2 = int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])

            # Assign team if not already assigned
            if track_id not in self.team_assignments:
                team = self._assign_team(frame, x1, y1, x2, y2)
                self.team_assignments[track_id] = team
            else:
                team = self.team_assignments[track_id]

            tracked_players.append((x1, y1, x2, y2, track_id, team))

        return tracked_players

    def _assign_team(self, frame: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> str:
        """
        Assign team based on jersey color.

        Args:
            frame: Video frame
            x1, y1, x2, y2: Player bounding box

        Returns:
            'home' or 'away'
        """
        # Extract player crop
        player_crop = frame[y1:y2, x1:x2]

        if player_crop.size == 0:
            return 'unknown'

        # Simple approach: analyze dominant color in upper half (jersey area)
        upper_half = player_crop[:int(player_crop.shape[0] * 0.5), :]

        # Get dominant color using mean
        avg_color = np.mean(upper_half.reshape(-1, 3), axis=0)

        # Heuristic: darker jerseys = away team (this is simplified)
        # In reality, you'd want to train a classifier or use more sophisticated color clustering
        brightness = np.mean(avg_color)

        return 'away' if brightness < 100 else 'home'

    def get_team_colors(self, frame: np.ndarray, tracks: List[Tuple[int, int, int, int, int, str]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate team colors from tracked players.

        Args:
            frame: Current frame
            tracks: List of tracked players

        Returns:
            Tuple of (home_color, away_color) as RGB arrays
        """
        home_colors = []
        away_colors = []

        for x1, y1, x2, y2, track_id, team in tracks:
            player_crop = frame[y1:y2, x1:x2]
            if player_crop.size == 0:
                continue

            upper_half = player_crop[:int(player_crop.shape[0] * 0.5), :]
            avg_color = np.mean(upper_half.reshape(-1, 3), axis=0)

            if team == 'home':
                home_colors.append(avg_color)
            elif team == 'away':
                away_colors.append(avg_color)

        home_color = np.mean(home_colors, axis=0) if home_colors else np.array([255, 255, 255])
        away_color = np.mean(away_colors, axis=0) if away_colors else np.array([0, 0, 0])

        return home_color, away_color

    def reset(self):
        """Reset tracker and team assignments."""
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            nms_max_overlap=0.7,
            max_cosine_distance=0.3,
            nn_budget=100
        )
        self.team_assignments = {}
