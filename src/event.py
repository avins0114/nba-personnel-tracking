"""Event class - a sequence of moments representing a play/possession."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

from .moment import Moment


@dataclass
class Event:
    """A sequence of moments representing a single play or possession.
    
    Attributes:
        event_id: Unique event identifier
        moments: List of Moment objects (25 per second)
        home_team: Home team info dict
        away_team: Away team info dict
        home_players_info: Player metadata for home team
        away_players_info: Player metadata for away team
    """
    event_id: int
    moments: List[Moment]
    home_team: Optional[Dict[str, Any]] = None
    away_team: Optional[Dict[str, Any]] = None
    home_players_info: Optional[List[Dict]] = None
    away_players_info: Optional[List[Dict]] = None
    
    @property
    def duration(self) -> float:
        """Duration of event in seconds."""
        if len(self.moments) < 2:
            return 0.0
        return self.moments[0].game_clock - self.moments[-1].game_clock
    
    @property
    def frame_count(self) -> int:
        """Number of frames in this event."""
        return len(self.moments)
    
    @property
    def home_team_id(self) -> Optional[int]:
        """Get home team ID."""
        if self.home_team:
            return self.home_team.get('teamid')
        return None
    
    @property
    def away_team_id(self) -> Optional[int]:
        """Get away team ID."""
        if self.away_team:
            return self.away_team.get('teamid')
        return None
    
    def get_moment(self, index: int) -> Optional[Moment]:
        """Get moment at specific index."""
        if 0 <= index < len(self.moments):
            return self.moments[index]
        return None
    
    # =========== TIME SERIES METRICS ===========
    
    def spacing_over_time(self, team_id: int, 
                          attacking_left: bool = True) -> List[float]:
        """Get spacing score for each moment.
        
        Args:
            team_id: Team to track
            attacking_left: Direction of attack
            
        Returns:
            List of spacing scores aligned with moments
        """
        return [m.spacing_score(team_id, attacking_left) for m in self.moments]
    
    def hull_area_over_time(self, team_id: int) -> List[float]:
        """Get convex hull area for each moment."""
        return [m.convex_hull_area(team_id) for m in self.moments]
    
    def avg_defender_distance_over_time(self, offensive_team_id: int,
                                         defensive_team_id: int) -> List[float]:
        """Track average defender distance across all offensive players."""
        result = []
        for moment in self.moments:
            attention = moment.defensive_attention_map(offensive_team_id, 
                                                       defensive_team_id)
            if attention:
                avg_dist = sum(d for _, d in attention) / len(attention)
                result.append(avg_dist)
            else:
                result.append(0.0)
        return result
    
    # =========== SUMMARY STATISTICS ===========
    
    def average_spacing(self, team_id: int, attacking_left: bool = True) -> float:
        """Get average spacing score across all moments."""
        scores = self.spacing_over_time(team_id, attacking_left)
        return np.mean(scores) if scores else 0.0
    
    def max_spacing(self, team_id: int, attacking_left: bool = True) -> float:
        """Get maximum spacing score achieved."""
        scores = self.spacing_over_time(team_id, attacking_left)
        return np.max(scores) if scores else 0.0
    
    def spacing_variance(self, team_id: int, attacking_left: bool = True) -> float:
        """Get variance in spacing (measure of movement/dynamism)."""
        scores = self.spacing_over_time(team_id, attacking_left)
        return np.var(scores) if scores else 0.0
    
    def open_shot_moments(self, player_id: int, defensive_team_id: int,
                          threshold: float = 6.0) -> int:
        """Count moments where a specific player had an open shot."""
        count = 0
        for moment in self.moments:
            for player in moment.players:
                if player.player_id == player_id:
                    if moment.open_shot_check(player, defensive_team_id, threshold):
                        count += 1
                    break
        return count
    
    def get_metrics_summary(self, offensive_team_id: int, 
                            defensive_team_id: int,
                            attacking_left: bool = True) -> Dict[str, float]:
        """Get a summary of all metrics for this event.
        
        Returns dict with:
            - avg_spacing: Average spacing score
            - max_spacing: Max spacing achieved
            - spacing_variance: Variance in spacing
            - avg_hull_area: Average convex hull area
            - avg_pairwise_dist: Average pairwise distance
            - avg_defender_dist: Average nearest defender distance
            - open_shot_pct: Percentage of moments with any open player
        """
        spacing_scores = self.spacing_over_time(offensive_team_id, attacking_left)
        hull_areas = self.hull_area_over_time(offensive_team_id)
        
        # Calculate pairwise distances
        pairwise = [m.average_pairwise_distance(offensive_team_id) 
                    for m in self.moments]
        
        # Defender distances
        def_dists = self.avg_defender_distance_over_time(offensive_team_id, 
                                                          defensive_team_id)
        
        # Open shot percentage
        open_moments = 0
        for moment in self.moments:
            offense = moment.get_team_players(offensive_team_id)
            if any(moment.open_shot_check(p, defensive_team_id) for p in offense):
                open_moments += 1
        
        return {
            'avg_spacing': np.mean(spacing_scores) if spacing_scores else 0,
            'max_spacing': np.max(spacing_scores) if spacing_scores else 0,
            'spacing_variance': np.var(spacing_scores) if spacing_scores else 0,
            'avg_hull_area': np.mean(hull_areas) if hull_areas else 0,
            'avg_pairwise_dist': np.mean(pairwise) if pairwise else 0,
            'avg_defender_dist': np.mean(def_dists) if def_dists else 0,
            'open_shot_pct': (open_moments / len(self.moments) * 100) if self.moments else 0,
            'duration_seconds': self.duration,
            'frame_count': self.frame_count
        }
