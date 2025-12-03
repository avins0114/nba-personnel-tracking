"""Basketball court drawing utilities for matplotlib."""
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
import numpy as np


class Court:
    """NBA court dimensions and drawing utilities.
    
    Court is 94 x 50 feet. Origin (0,0) is bottom-left corner.
    """
    
    # Court dimensions in feet
    WIDTH = 94
    HEIGHT = 50
    
    # Key dimensions
    PAINT_WIDTH = 16
    PAINT_LENGTH = 19
    THREE_POINT_RADIUS = 23.75
    THREE_POINT_CORNER_DIST = 22
    THREE_POINT_CORNER_LENGTH = 14
    FREE_THROW_RADIUS = 6
    BASKET_X = 5.25  # Distance from baseline to center of basket
    BASKET_Y = HEIGHT / 2
    
    # Colors
    COURT_COLOR = '#F5E6C8'
    LINE_COLOR = '#333333'
    PAINT_COLOR = '#E8D4B8'
    
    @classmethod
    def draw(cls, ax: plt.Axes, half_court: bool = False) -> plt.Axes:
        """Draw a basketball court on the given axes.
        
        Args:
            ax: Matplotlib axes to draw on
            half_court: If True, only draw half court (0-47 x 0-50)
        
        Returns:
            The axes with court drawn
        """
        # Set court color
        ax.set_facecolor(cls.COURT_COLOR)
        
        width = cls.WIDTH / 2 if half_court else cls.WIDTH
        
        # Court outline
        ax.plot([0, width], [0, 0], color=cls.LINE_COLOR, linewidth=2)
        ax.plot([0, width], [cls.HEIGHT, cls.HEIGHT], color=cls.LINE_COLOR, linewidth=2)
        ax.plot([0, 0], [0, cls.HEIGHT], color=cls.LINE_COLOR, linewidth=2)
        ax.plot([width, width], [0, cls.HEIGHT], color=cls.LINE_COLOR, linewidth=2)
        
        # Draw left side elements
        cls._draw_half_court_elements(ax, left_side=True)
        
        # Draw right side elements (if full court)
        if not half_court:
            cls._draw_half_court_elements(ax, left_side=False)
            # Center court line
            ax.plot([cls.WIDTH/2, cls.WIDTH/2], [0, cls.HEIGHT], 
                   color=cls.LINE_COLOR, linewidth=2)
            # Center circle
            center_circle = Circle((cls.WIDTH/2, cls.HEIGHT/2), 6, 
                                  fill=False, color=cls.LINE_COLOR, linewidth=2)
            ax.add_patch(center_circle)
        
        # Set axis properties
        ax.set_xlim(-2, width + 2)
        ax.set_ylim(-2, cls.HEIGHT + 2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        return ax
    
    @classmethod
    def _draw_half_court_elements(cls, ax: plt.Axes, left_side: bool = True):
        """Draw elements for one half of the court."""
        if left_side:
            basket_x = cls.BASKET_X
            paint_x = 0
            arc_angle1, arc_angle2 = -90, 90
        else:
            basket_x = cls.WIDTH - cls.BASKET_X
            paint_x = cls.WIDTH - cls.PAINT_LENGTH
            arc_angle1, arc_angle2 = 90, 270
        
        center_y = cls.HEIGHT / 2
        
        # Paint/key
        paint = Rectangle((paint_x, center_y - cls.PAINT_WIDTH/2), 
                          cls.PAINT_LENGTH, cls.PAINT_WIDTH,
                          fill=True, facecolor=cls.PAINT_COLOR,
                          edgecolor=cls.LINE_COLOR, linewidth=2)
        ax.add_patch(paint)
        
        # Free throw circle
        ft_circle = Arc((paint_x + cls.PAINT_LENGTH if left_side else paint_x, center_y),
                        cls.FREE_THROW_RADIUS * 2, cls.FREE_THROW_RADIUS * 2,
                        angle=0, theta1=arc_angle1, theta2=arc_angle2,
                        color=cls.LINE_COLOR, linewidth=2)
        ax.add_patch(ft_circle)
        
        # Basket
        basket = Circle((basket_x, center_y), 0.75, 
                        fill=False, color=cls.LINE_COLOR, linewidth=2)
        ax.add_patch(basket)
        
        # Backboard
        if left_side:
            ax.plot([4, 4], [center_y - 3, center_y + 3], 
                   color=cls.LINE_COLOR, linewidth=3)
        else:
            ax.plot([cls.WIDTH - 4, cls.WIDTH - 4], [center_y - 3, center_y + 3],
                   color=cls.LINE_COLOR, linewidth=3)
        
        # Three-point line
        # Corner threes (straight lines)
        corner_y_top = center_y + cls.THREE_POINT_CORNER_DIST
        corner_y_bottom = center_y - cls.THREE_POINT_CORNER_DIST
        
        if left_side:
            ax.plot([0, cls.THREE_POINT_CORNER_LENGTH], 
                   [corner_y_top, corner_y_top], color=cls.LINE_COLOR, linewidth=2)
            ax.plot([0, cls.THREE_POINT_CORNER_LENGTH], 
                   [corner_y_bottom, corner_y_bottom], color=cls.LINE_COLOR, linewidth=2)
        else:
            ax.plot([cls.WIDTH, cls.WIDTH - cls.THREE_POINT_CORNER_LENGTH],
                   [corner_y_top, corner_y_top], color=cls.LINE_COLOR, linewidth=2)
            ax.plot([cls.WIDTH, cls.WIDTH - cls.THREE_POINT_CORNER_LENGTH],
                   [corner_y_bottom, corner_y_bottom], color=cls.LINE_COLOR, linewidth=2)
        
        # Three-point arc
        arc_center_x = basket_x
        arc = Arc((arc_center_x, center_y),
                  cls.THREE_POINT_RADIUS * 2, cls.THREE_POINT_RADIUS * 2,
                  angle=0, 
                  theta1=arc_angle1 + 22 if left_side else arc_angle1 - 22,
                  theta2=arc_angle2 - 22 if left_side else arc_angle2 + 22,
                  color=cls.LINE_COLOR, linewidth=2)
        ax.add_patch(arc)
        
        # Restricted area
        restricted = Arc((basket_x, center_y), 8, 8,
                        angle=0, theta1=arc_angle1, theta2=arc_angle2,
                        color=cls.LINE_COLOR, linewidth=2)
        ax.add_patch(restricted)


def create_court_figure(half_court: bool = False, figsize: tuple = (12, 7)) -> tuple:
    """Create a new figure with a basketball court.
    
    Args:
        half_court: If True, draw only half court
        figsize: Figure size in inches
        
    Returns:
        Tuple of (figure, axes)
    """
    if half_court:
        figsize = (figsize[0] / 2, figsize[1])
    
    fig, ax = plt.subplots(figsize=figsize)
    Court.draw(ax, half_court=half_court)
    return fig, ax
