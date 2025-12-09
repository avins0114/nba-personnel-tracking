"""Manual player selection for initializing tracking."""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class ManualPlayerSelector:
    """Interactive player selection interface."""

    def __init__(self, frame: np.ndarray):
        """
        Initialize selector with a frame.

        Args:
            frame: Video frame to select players from
        """
        self.frame = frame.copy()
        self.display_frame = frame.copy()
        self.selections = []
        self.current_team = 'home'
        self.home_count = 0
        self.away_count = 0
        self.ball_selected = False

        # Selection state
        self.selecting_box = False
        self.box_start = None
        self.box_end = None

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for player selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Start selection box
            self.selecting_box = True
            self.box_start = (x, y)
            self.box_end = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selecting_box:
                # Update selection box
                self.box_end = (x, y)
                self._update_display()

        elif event == cv2.EVENT_LBUTTONUP:
            # Finalize selection
            if self.selecting_box:
                self.box_end = (x, y)
                self.selecting_box = False

                # Add selection
                x1 = min(self.box_start[0], self.box_end[0])
                y1 = min(self.box_start[1], self.box_end[1])
                x2 = max(self.box_start[0], self.box_end[0])
                y2 = max(self.box_start[1], self.box_end[1])

                # Ensure box has some size
                if x2 - x1 > 5 and y2 - y1 > 5:
                    self._add_selection(x1, y1, x2, y2)

                self._update_display()

    def _add_selection(self, x1: int, y1: int, x2: int, y2: int):
        """Add a player/ball selection."""
        if self.ball_selected:
            print("All selections complete! Press ENTER to continue.")
            return

        if self.current_team == 'home':
            if self.home_count >= 5:
                print("5 home players already selected. Switching to away team...")
                self.current_team = 'away'
            else:
                team = 'home'
                label = f"H{self.home_count + 1}"
                color = (0, 0, 255)  # Red for home
                self.selections.append({
                    'bbox': (x1, y1, x2, y2),
                    'team': team,
                    'label': label,
                    'type': 'player'
                })
                self.home_count += 1
                print(f"Selected {label} (Home player {self.home_count}/5)")

        if self.current_team == 'away' and not self.ball_selected:
            if self.away_count >= 5:
                print("5 away players selected. Now select the ball...")
                self.current_team = 'ball'
            else:
                team = 'away'
                label = f"A{self.away_count + 1}"
                color = (255, 0, 0)  # Blue for away
                self.selections.append({
                    'bbox': (x1, y1, x2, y2),
                    'team': team,
                    'label': label,
                    'type': 'player'
                })
                self.away_count += 1
                print(f"Selected {label} (Away player {self.away_count}/5)")

        if self.current_team == 'ball' and not self.ball_selected:
            self.selections.append({
                'bbox': (x1, y1, x2, y2),
                'team': 'ball',
                'label': 'BALL',
                'type': 'ball'
            })
            self.ball_selected = True
            print("Ball selected! Press ENTER to continue.")

    def _update_display(self):
        """Update the display with current selections."""
        self.display_frame = self.frame.copy()

        # Draw existing selections
        for sel in self.selections:
            x1, y1, x2, y2 = sel['bbox']
            if sel['type'] == 'ball':
                color = (0, 255, 255)  # Yellow for ball
            elif sel['team'] == 'home':
                color = (0, 0, 255)  # Red for home
            else:
                color = (255, 0, 0)  # Blue for away

            cv2.rectangle(self.display_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(self.display_frame, sel['label'],
                       (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 2)

        # Draw current selection box
        if self.selecting_box and self.box_start and self.box_end:
            x1 = min(self.box_start[0], self.box_end[0])
            y1 = min(self.box_start[1], self.box_end[1])
            x2 = max(self.box_start[0], self.box_end[0])
            y2 = max(self.box_start[1], self.box_end[1])
            cv2.rectangle(self.display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Add instructions
        self._draw_instructions()

        cv2.imshow('Select Players', self.display_frame)

    def _draw_instructions(self):
        """Draw instruction text on the display."""
        instructions = []

        if self.home_count < 5:
            instructions.append(f"Select HOME player {self.home_count + 1}/5 (RED)")
        elif self.away_count < 5:
            instructions.append(f"Select AWAY player {self.away_count + 1}/5 (BLUE)")
        elif not self.ball_selected:
            instructions.append("Select BALL (YELLOW)")
        else:
            instructions.append("All selected! Press ENTER to continue")

        instructions.append("ESC to cancel")

        y_offset = 30
        for instruction in instructions:
            cv2.putText(self.display_frame, instruction,
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 0), 2)
            y_offset += 30

    def select_players(self) -> Optional[List[dict]]:
        """
        Run interactive player selection.

        Returns:
            List of selection dictionaries with bbox, team, label, type
            or None if cancelled
        """
        cv2.namedWindow('Select Players')
        cv2.setMouseCallback('Select Players', self.mouse_callback)

        print("\n=== Manual Player Selection ===")
        print("Instructions:")
        print("  1. Click and drag to draw a box around each player")
        print("  2. Select 5 HOME players (will show as RED)")
        print("  3. Select 5 AWAY players (will show as BLUE)")
        print("  4. Select the BALL (will show as YELLOW)")
        print("  5. Press ENTER when done, ESC to cancel")
        print()

        self._update_display()

        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("\nSelection cancelled.")
                cv2.destroyAllWindows()
                return None

            if key == 13:  # ENTER
                if self.ball_selected:
                    print(f"\nSelection complete: {self.home_count} home, {self.away_count} away, 1 ball")
                    cv2.destroyAllWindows()
                    return self.selections
                else:
                    print("Please complete all selections first.")

        return None

    def get_detections_for_tracker(self) -> List[Tuple[int, int, int, int, float]]:
        """
        Convert selections to detection format for tracker.

        Returns:
            List of (x1, y1, x2, y2, confidence) for DeepSORT
        """
        detections = []
        for sel in self.selections:
            if sel['type'] == 'player':  # Don't include ball in player tracking
                x1, y1, x2, y2 = sel['bbox']
                detections.append((x1, y1, x2, y2, 1.0))  # Confidence = 1.0 for manual
        return detections

    def get_team_assignments(self) -> dict:
        """
        Get team assignments for each selection.

        Returns:
            Dictionary mapping selection index to team ('home' or 'away')
        """
        assignments = {}
        for i, sel in enumerate(self.selections):
            if sel['type'] == 'player':
                assignments[i] = sel['team']
        return assignments

    def get_ball_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """Get ball bounding box if selected."""
        for sel in self.selections:
            if sel['type'] == 'ball':
                return sel['bbox']
        return None
