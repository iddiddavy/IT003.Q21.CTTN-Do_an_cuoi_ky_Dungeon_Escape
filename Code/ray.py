import math, pygame
from settings import *
from map import Map
from player import Player

def normalize_angle(angle):
    """Normalizes an angle to the range [0, 2*pi]."""
    angle = angle % (2 * math.pi)
    if (angle <= 0):
        angle = (2 * math.pi) + angle
    return angle

def distance_between(x1, y1, x2, y2):
    """Calculates the Euclidean distance between two points."""
    return math.sqrt((x2 - x1)*(x2 - x1) + (y2 - y1)*(y2 - y1))     


class Ray:
    """
    Simulates a single light ray in the Ray Casting system.
    Calculates the ray's trajectory and stores intersection results with the environment.
    """

    def __init__(self, angle, player, map):
        """Initializes a ray from the player's position with a specific cast angle."""
        self.rayAngle = normalize_angle(angle)
        self.player: Player = player
        self.map: Map = map

        self.is_facing_down = self.rayAngle > 0 and self.rayAngle < math.pi
        self.is_facing_up = not self.is_facing_down
        self.is_facing_right = self.rayAngle < 0.5 * math.pi or self.rayAngle > 1.5 * math.pi
        self.is_facing_left = not self.is_facing_right

        self.wall_hit_x = 0
        self.wall_hit_y = 0
        self.distance = 0
        self.was_hit_vertical = False
        self.wall_offset = 0
        self.hit_content = 0

    def cast(self):
        """
        Executes the ray casting logic using the DDA algorithm for both horizontal and vertical axes.
        Identifies the nearest collision point with world geometry.
        """
        # HORIZONTAL INTERSECTION CHECK
        found_horizontal_wall = False
        horizontal_hit_x = 0
        horizontal_hit_y = 0
        horizontal_content = 0

        if self.is_facing_up:
            first_intersection_y = ((self.player.y // TILESIZE) * TILESIZE) - 0.0001
        elif self.is_facing_down:
            first_intersection_y = ((self.player.y // TILESIZE) * TILESIZE) + TILESIZE

        first_intersection_x = self.player.x + (first_intersection_y - self.player.y) / math.tan(self.rayAngle)

        nextHorizontalX = first_intersection_x
        nextHorizontalY = first_intersection_y

        ya = -TILESIZE if self.is_facing_up else TILESIZE
        xa = ya / math.tan(self.rayAngle)

        map_width_px = COLS * TILESIZE
        map_height_px = ROWS * TILESIZE

        while (0 <= nextHorizontalX <= map_width_px and 0 <= nextHorizontalY <= map_height_px): 
            grid_x = int(nextHorizontalX // TILESIZE)
            grid_y = int(nextHorizontalY // TILESIZE)
            if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                content = self.map.grid[grid_y][grid_x]
                if content > 0:
                    found_horizontal_wall = True
                    horizontal_hit_x = nextHorizontalX
                    horizontal_hit_y = nextHorizontalY
                    horizontal_content = content
                    break
            nextHorizontalX += xa
            nextHorizontalY += ya

        # VERTICAL INTERSECTION CHECK
        found_vertical_wall = False
        vertical_hit_x = 0
        vertical_hit_y = 0
        vertical_content = 0

        if self.is_facing_right:
            first_intersection_x = ((self.player.x // TILESIZE) * TILESIZE) + TILESIZE
        elif self.is_facing_left:
            first_intersection_x = ((self.player.x // TILESIZE) * TILESIZE) - 0.0001

        first_intersection_y = self.player.y + (first_intersection_x - self.player.x) * math.tan(self.rayAngle)

        nextVerticalX = first_intersection_x
        nextVerticalY = first_intersection_y

        xa = TILESIZE if self.is_facing_right else -TILESIZE
        ya = xa * math.tan(self.rayAngle)

        while (0 <= nextVerticalX <= map_width_px and 0 <= nextVerticalY <= map_height_px):
            grid_x = int(nextVerticalX // TILESIZE)
            grid_y = int(nextVerticalY // TILESIZE)
            if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                content = self.map.grid[grid_y][grid_x]
                if content > 0:
                    found_vertical_wall = True
                    vertical_hit_x = nextVerticalX
                    vertical_hit_y = nextVerticalY
                    vertical_content = content
                    break
            nextVerticalX += xa
            nextVerticalY += ya

        # CHOOSE THE NEAREST HIT
        h_dist = distance_between(self.player.x, self.player.y, horizontal_hit_x, horizontal_hit_y) if found_horizontal_wall else 99999
        v_dist = distance_between(self.player.x, self.player.y, vertical_hit_x, vertical_hit_y) if found_vertical_wall else 99999

        if h_dist < v_dist:
            self.wall_hit_x, self.wall_hit_y, self.distance = horizontal_hit_x, horizontal_hit_y, h_dist
            self.was_hit_vertical = False
            self.wall_offset = self.wall_hit_x % TILESIZE
            self.hit_content = horizontal_content
        else:
            self.wall_hit_x, self.wall_hit_y, self.distance = vertical_hit_x, vertical_hit_y, v_dist
            self.was_hit_vertical = True
            self.wall_offset = self.wall_hit_y % TILESIZE
            self.hit_content = vertical_content

        self.wall_offset /= TILESIZE

    def render(self, screen):
        """Draws the ray on the screen (primarily for Mini-map/Debug modes)."""
        pygame.draw.line(screen, (255, 0, 0),
                         (self.player.x, self.player.y),
                         (self.wall_hit_x, self.wall_hit_y))        
