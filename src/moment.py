"""Moment class - a single frame/snapshot of game state."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
from scipy.spatial import ConvexHull

from .player import Player
from .ball import Ball


@dataclass
class Moment:
    """A single snapshot in time containing all player and ball positions.
    
    SportVU captures 25 moments per second.
    
    Attributes:
        quarter: Game quarter (1-4, 5+ for OT)
        game_clock: Seconds remaining in quarter
        shot_clock: Seconds remaining on shot clock
        ball: Ball object with position
        players: List of 10 Player objects
        home_team_id: Team ID of home team
        away_team_id: Team ID of away team
    """
    quarter: int
    game_clock: float
    shot_clock: Optional[float]
    ball: Ball
    players: List[Player]
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    
    @property
    def home_players(self) -> List[Player]:
        """Get list of home team players."""
        if self.home_team_id is None:
            return []
        return [p for p in self.players if p.team_id == self.home_team_id]
    
    @property
    def away_players(self) -> List[Player]:
        """Get list of away team players."""
        if self.away_team_id is None:
            return []
        return [p for p in self.players if p.team_id == self.away_team_id]
    
    def get_team_players(self, team_id: int) -> List[Player]:
        """Get players for a specific team."""
        return [p for p in self.players if p.team_id == team_id]
    
    def get_ball_handler(self, threshold: float = 3.0) -> Optional[Player]:
        """Find the player closest to the ball (likely ball handler).
        
        Args:
            threshold: Maximum distance to be considered ball handler
        """
        closest = None
        min_dist = float('inf')
        
        for player in self.players:
            dist = player.distance_to_point(self.ball.x, self.ball.y)
            if dist < min_dist:
                min_dist = dist
                closest = player
        
        if min_dist <= threshold:
            return closest
        return None
    
    def get_offensive_team_id(self) -> Optional[int]:
        """Determine which team has possession based on ball proximity."""
        handler = self.get_ball_handler()
        if handler:
            return handler.team_id
        return None
    
    # =========== SPACING METRICS ===========
    
    def convex_hull_area(self, team_id: int) -> float:
        """Calculate the convex hull area for a team's players.
        
        Larger area = better spacing.
        
        Args:
            team_id: Team to calculate hull for
            
        Returns:
            Area in square feet
        """
        players = self.get_team_players(team_id)
        if len(players) < 3:
            return 0.0
        
        points = np.array([[p.x, p.y] for p in players])
        try:
            hull = ConvexHull(points)
            return hull.volume  # In 2D, volume gives area
        except Exception:
            return 0.0
    
    def average_pairwise_distance(self, team_id: int) -> float:
        """Calculate average distance between all pairs of teammates.
        
        Args:
            team_id: Team to calculate for
            
        Returns:
            Average distance in feet
        """
        players = self.get_team_players(team_id)
        if len(players) < 2:
            return 0.0
        
        total_dist = 0.0
        count = 0
        
        for i, p1 in enumerate(players):
            for p2 in players[i+1:]:
                total_dist += p1.distance_to(p2)
                count += 1
        
        return total_dist / count if count > 0 else 0.0
    
    def paint_player_count(self, team_id: int, attacking_left: bool = True) -> int:
        """Count how many players from a team are in the paint.
        
        Args:
            team_id: Team to count
            attacking_left: True if team is attacking left basket
        """
        players = self.get_team_players(team_id)
        return sum(1 for p in players if p.is_in_paint(left_basket=attacking_left))
    
    def three_point_spread(self, team_id: int, attacking_left: bool = True) -> int:
        """Count players beyond the 3-point line.
        
        Args:
            team_id: Team to count
            attacking_left: True if team is attacking left basket
        """
        players = self.get_team_players(team_id)
        return sum(1 for p in players if p.is_beyond_arc(left_basket=attacking_left))
    
    # =========== GRAVITY METRICS ===========
    
    def nearest_defender_distance(self, player: Player, defending_team_id: int) -> float:
        """Find distance to the nearest defender for a player.
        
        Args:
            player: Offensive player
            defending_team_id: Team ID of defense
            
        Returns:
            Distance in feet to nearest defender
        """
        defenders = self.get_team_players(defending_team_id)
        if not defenders:
            return float('inf')
        
        return min(player.distance_to(d) for d in defenders)
    
    def defensive_attention_map(self, offensive_team_id: int, 
                                 defensive_team_id: int) -> List[Tuple[Player, float]]:
        """Get defensive attention (nearest defender distance) for each offensive player.
        
        Args:
            offensive_team_id: Team on offense
            defensive_team_id: Team on defense
            
        Returns:
            List of (player, nearest_defender_distance) tuples
        """
        offense = self.get_team_players(offensive_team_id)
        return [(p, self.nearest_defender_distance(p, defensive_team_id)) 
                for p in offense]
    
    def help_defender_distances(self, defensive_team_id: int) -> List[float]:
        """Calculate distances of all defenders to the ball.
        
        Useful for measuring help defense positioning.
        
        Returns:
            List of distances sorted ascending
        """
        defenders = self.get_team_players(defensive_team_id)
        distances = [d.distance_to_point(self.ball.x, self.ball.y) 
                     for d in defenders]
        return sorted(distances)
    
    def open_shot_check(self, player: Player, defending_team_id: int,
                        threshold: float = 6.0) -> bool:
        """Check if a player has an open shot (no defender within threshold).
        
        Args:
            player: Player to check
            defending_team_id: Team on defense
            threshold: Distance in feet to be considered "open"
        """
        return self.nearest_defender_distance(player, defending_team_id) >= threshold
    
    # =========== COMPOSITE METRICS ===========
    
    def spacing_score(self, team_id: int, attacking_left: bool = True) -> float:
        """Calculate a composite spacing score.
        
        Combines hull area, pairwise distance, and 3pt spread.
        Higher = better spacing.
        
        Returns:
            Normalized score (roughly 0-100)
        """
        hull = self.convex_hull_area(team_id)
        pairwise = self.average_pairwise_distance(team_id)
        spread_3 = self.three_point_spread(team_id, attacking_left)
        paint_count = self.paint_player_count(team_id, attacking_left)
        
        # Normalize components
        # Good hull area: 400-800 sq ft -> 0.5-1.0
        hull_score = min(hull / 800, 1.0)
        
        # Good pairwise: 15-25 ft -> 0.5-1.0
        pairwise_score = min(pairwise / 25, 1.0)
        
        # 3pt spread: 0-4 players -> 0-1.0
        spread_score = spread_3 / 4
        
        # Paint density penalty: fewer is better for spacing
        paint_penalty = max(0, (paint_count - 1) * 0.1)
        
        # Weighted combination
        score = (hull_score * 0.3 + 
                 pairwise_score * 0.3 + 
                 spread_score * 0.3 - 
                 paint_penalty) * 100
        
        return max(0, min(100, score))
