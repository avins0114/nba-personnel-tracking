"""Player class for NBA tracking data."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Player:
    """Represents a player at a single moment in time.
    
    Attributes:
        team_id: NBA team ID
        player_id: NBA player ID
        x: X coordinate on court (0-94 feet)
        y: Y coordinate on court (0-50 feet)
        firstname: Player's first name (if available)
        lastname: Player's last name (if available)
        jersey: Jersey number (if available)
        position: Position abbreviation (if available)
    """
    team_id: int
    player_id: int
    x: float
    y: float
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    jersey: Optional[str] = None
    position: Optional[str] = None
    
    @property
    def name(self) -> str:
        """Full name or player ID if name unavailable."""
        if self.firstname and self.lastname:
            return f"{self.firstname} {self.lastname}"
        elif self.lastname:
            return self.lastname
        return str(self.player_id)
    
    @property
    def coords(self) -> tuple:
        """Return (x, y) coordinates."""
        return (self.x, self.y)
    
    def distance_to(self, other: 'Player') -> float:
        """Calculate Euclidean distance to another player."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate distance to a specific point."""
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5
    
    def is_in_paint(self, left_basket: bool = True) -> bool:
        """Check if player is in the paint.
        
        Args:
            left_basket: True if checking left side paint
        """
        paint_y_min = 25 - 8  # center - half paint width
        paint_y_max = 25 + 8
        
        if left_basket:
            return 0 <= self.x <= 19 and paint_y_min <= self.y <= paint_y_max
        else:
            return 75 <= self.x <= 94 and paint_y_min <= self.y <= paint_y_max
    
    def is_beyond_arc(self, left_basket: bool = True) -> bool:
        """Check if player is beyond the 3-point arc.
        
        Args:
            left_basket: True if shooting at left basket
        """
        basket_x = 5.25 if left_basket else 88.75
        basket_y = 25
        
        dist_to_basket = ((self.x - basket_x) ** 2 + (self.y - basket_y) ** 2) ** 0.5
        
        # Corner 3s are closer (22 ft) than arc (23.75 ft)
        if self.y < 3 or self.y > 47:
            return dist_to_basket >= 22
        return dist_to_basket >= 23.75
