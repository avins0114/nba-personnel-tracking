"""Ball class for NBA tracking data."""
from dataclasses import dataclass


@dataclass
class Ball:
    """Represents the basketball at a single moment in time.
    
    Attributes:
        x: X coordinate on court (0-94 feet)
        y: Y coordinate on court (0-50 feet)
        radius: Height of ball above court (used to detect shots/passes)
    """
    x: float
    y: float
    radius: float = 0.0
    
    # Ball ID in SportVU data is -1
    BALL_ID = -1
    
    @property
    def coords(self) -> tuple:
        """Return (x, y) coordinates."""
        return (self.x, self.y)
    
    @property
    def height(self) -> float:
        """Alias for radius (height above floor)."""
        return self.radius
    
    def is_in_air(self, threshold: float = 8.0) -> bool:
        """Check if ball is elevated (shot or pass in progress).
        
        Args:
            threshold: Height in feet to consider "in air"
        """
        return self.radius > threshold
    
    def distance_to_basket(self, left_basket: bool = True) -> float:
        """Calculate distance to the basket.
        
        Args:
            left_basket: True for left side basket
        """
        basket_x = 5.25 if left_basket else 88.75
        basket_y = 25
        return ((self.x - basket_x) ** 2 + (self.y - basket_y) ** 2) ** 0.5
