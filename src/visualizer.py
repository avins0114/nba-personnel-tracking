"""Visualization utilities for NBA tracking data."""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
from matplotlib.animation import FuncAnimation
from matplotlib.collections import PatchCollection
import numpy as np
from typing import Optional, List, Tuple
from scipy.spatial import ConvexHull

from .court import Court, create_court_figure
from .event import Event
from .moment import Moment


# Team colors (subset of NBA teams)
TEAM_COLORS = {
    # Default
    'home': '#E31837',  # Red
    'away': '#17408B',  # Blue
    # Some specific teams
    1610612737: '#E03A3E',  # Hawks
    1610612738: '#007A33',  # Celtics
    1610612739: '#860038',  # Cavaliers
    1610612740: '#00788C',  # Pelicans
    1610612741: '#CE1141',  # Bulls
    1610612742: '#00538C',  # Mavericks
    1610612743: '#0E2240',  # Nuggets
    1610612744: '#1D428A',  # Warriors
    1610612745: '#CE1141',  # Rockets
    1610612746: '#C8102E',  # Clippers
    1610612747: '#552583',  # Lakers
    1610612748: '#98002E',  # Heat
    1610612749: '#00471B',  # Bucks
    1610612750: '#0C2340',  # Timberwolves
    1610612751: '#002B5C',  # Nets
    1610612752: '#006BB6',  # Knicks
    1610612753: '#0077C0',  # Magic
    1610612754: '#002D62',  # Pacers
    1610612755: '#006BB6',  # 76ers
    1610612756: '#1D1160',  # Suns
    1610612757: '#E03A3E',  # Blazers
    1610612758: '#5A2D81',  # Kings
    1610612759: '#C4CED4',  # Spurs
    1610612760: '#007AC1',  # Thunder
    1610612761: '#CE1141',  # Raptors
    1610612762: '#002B5C',  # Jazz
    1610612763: '#002B5C',  # Grizzlies
    1610612764: '#002B5C',  # Wizards
}


class GameVisualizer:
    """Visualize NBA tracking data with animations."""

    def __init__(self, event: Event, fps: int = 25, ax: Optional[plt.Axes] = None, video_frames: Optional[List[np.ndarray]] = None, half_court: bool = False):
        """Initialize visualizer.

        Args:
            event: Event to visualize
            fps: Frames per second (SportVU is 25)
            ax: Optional matplotlib axes to use (for comparison mode)
            video_frames: Optional list of video frames to display alongside court
            half_court: Whether to show only half court
        """
        self.event = event
        self.fps = fps
        self.fig = None
        self.ax = ax  # Allow external ax
        self.video_frames = video_frames
        self.video_ax = None  # Separate axis for video
        self.video_image = None  # Image object for video frames
        self.half_court = half_court
        self.show_spacing = False
        self.show_trails = False
        self.trail_length = 10

        # Animation elements (will be set up on first draw)
        self._player_circles = []
        self._player_labels = []
        self._ball_circle = None
        self._hull_patch = None
        self._spacing_text = None
        self._trail_lines = []

    def setup_figure(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create figure and draw court."""
        if self.ax is not None:
            # Use provided axes
            self.fig = self.ax.get_figure()
            # Draw court on provided axes
            from .court import Court
            Court.draw(self.ax, half_court=self.half_court)
        else:
            # Create new figure with optional video display
            if self.video_frames is not None:
                # Side-by-side layout: video on left, court on right
                from matplotlib.gridspec import GridSpec
                fig_width = 20 if not self.half_court else 16
                self.fig = plt.figure(figsize=(fig_width, 7))
                gs = GridSpec(1, 2, figure=self.fig, width_ratios=[1.2, 1])

                # Video axes (left)
                self.video_ax = self.fig.add_subplot(gs[0, 0])
                self.video_ax.set_title('Original Video', fontsize=14, fontweight='bold')
                self.video_ax.axis('off')

                # Court axes (right)
                self.ax = self.fig.add_subplot(gs[0, 1])
                from .court import Court
                Court.draw(self.ax, half_court=self.half_court)
                court_label = 'Half Court' if self.half_court else 'Full Court'
                self.ax.set_title(f'Tracked Players on {court_label}', fontsize=14, fontweight='bold')
            else:
                # Just court (original behavior)
                self.fig, self.ax = create_court_figure(half_court=self.half_court)
                fig_width = 7 if self.half_court else 14
                self.fig.set_size_inches(fig_width, 7)
        return self.fig, self.ax

    def _get_team_color(self, team_id: int, is_home: bool) -> str:
        """Get color for a team."""
        if team_id in TEAM_COLORS:
            return TEAM_COLORS[team_id]
        return TEAM_COLORS['home'] if is_home else TEAM_COLORS['away']

    def _init_animation(self):
        """Initialize animation elements."""
        if not self.event.moments:
            return

        moment = self.event.moments[0]
        home_id = self.event.home_team_id

        # Clear any existing elements
        self._player_circles = []
        self._player_labels = []

        # Create player circles and labels
        for player in moment.players:
            is_home = player.team_id == home_id
            color = self._get_team_color(player.team_id, is_home)

            circle = Circle((player.x, player.y), 2.5,
                           color=color, alpha=0.8, zorder=3)
            self.ax.add_patch(circle)
            self._player_circles.append(circle)

            label = self.ax.text(player.x, player.y,
                                player.jersey or '',
                                ha='center', va='center',
                                fontsize=8, color='white',
                                fontweight='bold', zorder=4)
            self._player_labels.append(label)

        # Ball
        self._ball_circle = Circle((moment.ball.x, moment.ball.y), 1.2,
                                   color='#FF6B00', alpha=0.9, zorder=5)
        self.ax.add_patch(self._ball_circle)

        # Convex hull for spacing visualization
        self._hull_patch = self.ax.fill([], [], alpha=0.2, color='green', zorder=1)[0]

        # Spacing score display
        self._spacing_text = self.ax.text(47, -3, '', fontsize=10,
                                          ha='center', va='top')

    def _update_animation(self, frame: int):
        """Update animation for a specific frame."""
        if frame >= len(self.event.moments):
            return

        moment = self.event.moments[frame]
        home_id = self.event.home_team_id
        away_id = self.event.away_team_id

        # Update video frame if available
        if self.video_frames is not None and self.video_ax is not None:
            if frame < len(self.video_frames):
                video_frame = self.video_frames[frame]
                # Convert BGR to RGB for matplotlib
                import cv2
                video_frame_rgb = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)

                if self.video_image is None:
                    # First frame - create image object
                    self.video_image = self.video_ax.imshow(video_frame_rgb, aspect='auto')
                else:
                    # Update existing image
                    self.video_image.set_data(video_frame_rgb)

        # Update player positions
        for i, player in enumerate(moment.players):
            if i < len(self._player_circles):
                self._player_circles[i].center = (player.x, player.y)
                self._player_labels[i].set_position((player.x, player.y))
                self._player_labels[i].set_text(player.jersey or '')

        # Update ball
        if self._ball_circle:
            self._ball_circle.center = (moment.ball.x, moment.ball.y)
            # Scale ball based on height
            radius = 1.2 + moment.ball.radius * 0.1
            self._ball_circle.set_radius(min(radius, 3))

        # Clock display removed - not needed for CV tracking
        # (SportVU data has accurate game clock, but CV tracking doesn't)

        # Update spacing visualization
        if self.show_spacing:
            # Determine offensive team (team with ball)
            off_team_id = moment.get_offensive_team_id()
            if off_team_id:
                def_team_id = away_id if off_team_id == home_id else home_id
                offense = moment.get_team_players(off_team_id)

                if len(offense) >= 3:
                    try:
                        points = np.array([[p.x, p.y] for p in offense])
                        hull = ConvexHull(points)
                        hull_points = points[hull.vertices]
                        self._hull_patch.set_xy(hull_points)
                    except Exception:
                        self._hull_patch.set_xy(np.empty((0, 2)))

                # Update spacing score
                attacking_left = off_team_id == home_id  # Simplified assumption
                score = moment.spacing_score(off_team_id, attacking_left)
                hull_area = moment.convex_hull_area(off_team_id)

                spacing_str = f"Spacing: {score:.1f} | Hull: {hull_area:.0f} sq ft"
                self._spacing_text.set_text(spacing_str)
            else:
                self._hull_patch.set_xy(np.empty((0, 2)))
                self._spacing_text.set_text('')

        artists = (self._player_circles + self._player_labels +
                   [self._ball_circle, self._hull_patch, self._spacing_text])
        if self.video_image is not None:
            artists.append(self.video_image)
        return artists

    def animate(self, show_spacing: bool = False,
                interval: Optional[int] = None,
                save_path: Optional[str] = None) -> FuncAnimation:
        """Create and optionally save animation.

        Args:
            show_spacing: If True, show convex hull overlay
            interval: Milliseconds between frames (default: 1000/fps)
            save_path: If provided, save animation to this path

        Returns:
            FuncAnimation object
        """
        self.show_spacing = show_spacing

        if interval is None:
            interval = int(1000 / self.fps)

        # Setup
        self.setup_figure()
        self._init_animation()

        # Create animation
        anim = FuncAnimation(
            self.fig,
            self._update_animation,
            frames=len(self.event.moments),
            interval=interval,
            blit=False,
            repeat=True
        )

        # Save if path provided
        if save_path:
            anim.save(save_path, writer='pillow', fps=self.fps)

        return anim

    def show_frame(self, frame_index: int, show_spacing: bool = True):
        """Display a single frame (no animation).

        Args:
            frame_index: Which frame to show
            show_spacing: Whether to show spacing overlay
        """
        self.show_spacing = show_spacing
        self.setup_figure()
        self._init_animation()
        self._update_animation(frame_index)
        plt.tight_layout()
        plt.show()


def visualize_event(event: Event,
                    show_spacing: bool = False,
                    save_path: Optional[str] = None) -> FuncAnimation:
    """Convenience function to visualize an event.

    Args:
        event: Event to visualize
        show_spacing: Whether to show spacing overlay
        save_path: Optional path to save animation

    Returns:
        FuncAnimation object
    """
    viz = GameVisualizer(event)
    return viz.animate(show_spacing=show_spacing, save_path=save_path)
