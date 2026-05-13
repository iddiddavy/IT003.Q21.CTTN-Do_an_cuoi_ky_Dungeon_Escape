import pygame
import math
from settings import *
from dungeon_generator import generate_dungeon
import random

class Map:
    """
    Manages the 2D grid-based world map.
    Responsible for storing spatial structures, providing data for the Raycaster,
    and handling collision detection for all game entities.
    """

    def __init__(self):
        """Initializes the map grid and loads layout data from the dungeon generator."""
        self.grid, self.spawn_room, self.all_rooms = generate_dungeon(ROWS, COLS)
        other_rooms = [room for room in self.all_rooms if room != self.spawn_room]
        if len(other_rooms) >= 2:
            key_room, exit_room = random.sample(other_rooms, 2)     
            self.key_pos = (key_room[0] + key_room[2]//2, key_room[1] + key_room[3]//2)
            self.exit_pos = (exit_room[0] + exit_room[2]//2, exit_room[1] + exit_room[3]//2)
        else:
            self.key_pos = None
            self.exit_pos = None

    def get_spawn_pos(self):
        """Returns the pixel coordinates of the spawn room's center."""
        x = (self.spawn_room[0] + self.spawn_room[2] // 2) * TILESIZE
        y = (self.spawn_room[1] + self.spawn_room[3] // 2) * TILESIZE
        return x, y

    def has_wall_at(self, x, y):
        """
        Checks if the provided coordinates (x, y) correspond to a wall tile.
        
        Args:
            x (float): World X-coordinate.
            y (float): World Y-coordinate.
        Returns:
            bool: True if it's a wall, False otherwise.
        """
        grid_x = int(x) // int(TILESIZE)
        grid_y = int(y) // int(TILESIZE)
        if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
            if grid_y < len(self.grid) and grid_x < len(self.grid[0]):
                return self.grid[grid_y][grid_x] == 1
        return True

    def has_wall_between(self, x1, y1, x2, y2):
        """Checks for any wall obstructions along the line segment from (x1, y1) to (x2, y2)."""
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if dist == 0: return False

        step_size = 4
        num_steps = int(dist / step_size)

        for i in range(1, num_steps):
            check_x = x1 + (x2 - x1) * (i / num_steps)
            check_y = y1 + (y2 - y1) * (i / num_steps)
            if self.has_wall_at(check_x, check_y):
                return True
        return False

    def render_minimap(self, screen):
        """Renders the top-down Mini-map on the screen, positioned at the top-right."""
        scale = MINIMAP_SCALE
        offset_x = WINDOW_WIDTH - (COLS * TILESIZE * scale) - 10
        offset_y = 10

        # Draw background for minimap
        pygame.draw.rect(screen, (0, 0, 0), (offset_x - 2, offset_y - 2, (COLS * TILESIZE * scale) + 4, (ROWS * TILESIZE * scale) + 4))
        pygame.draw.rect(screen, (100, 100, 100), (offset_x - 2, offset_y - 2, (COLS * TILESIZE * scale) + 4, (ROWS * TILESIZE * scale) + 4), 1)

        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                tile_x = offset_x + j * TILESIZE * scale
                tile_y = offset_y + i * TILESIZE * scale

                if self.grid[i][j] == 1: color = (60, 60, 60)
                else: color = (200, 200, 200)
                
                if self.grid[i][j] == 2: color = (255, 215, 0)      # Key
                if self.grid[i][j] == 3: color = (0, 255, 255)      # Exit

                pygame.draw.rect(screen, color, (tile_x, tile_y, TILESIZE * scale, TILESIZE * scale))

    def render(self, screen):
        """Renders the 2D grid map (primarily for debugging or 2D mode)."""
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                tile_x = j * TILESIZE
                tile_y = i * TILESIZE

                if self.grid[i][j] == 0:
                    pygame.draw.rect(screen, (255, 255, 255), (tile_x, tile_y, TILESIZE - 1, TILESIZE - 1))
                elif self.grid[i][j] == 1:
                    pygame.draw.rect(screen, (40, 40, 40), (tile_x, tile_y, TILESIZE - 1, TILESIZE - 1))
                elif self.grid[i][j] == 4:
                    pygame.draw.rect(screen, (139, 69, 19), (tile_x, tile_y, TILESIZE - 1, TILESIZE - 1))
        for j in range(len(self.grid[0])):
                tile_x = j * TILESIZE
                tile_y = i * TILESIZE

                if self.grid[i][j] == 0:
                    pygame.draw.rect(screen, (255, 255, 255), (tile_x, tile_y, TILESIZE - 1, TILESIZE - 1))
                elif self.grid[i][j] == 1:
                    pygame.draw.rect(screen, (40, 40, 40), (tile_x, tile_y, TILESIZE - 1, TILESIZE - 1))
