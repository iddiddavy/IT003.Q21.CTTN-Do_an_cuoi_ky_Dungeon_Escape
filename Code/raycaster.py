import pygame
from settings import *
from ray import Ray
import random
import math

class RayCaster:
    """
    Primary Rendering Engine.
    Uses the DDA algorithm to project 2D collision data into a Pseudo-3D perspective.
    Handles wall rendering, texture mapping, and depth shading.
    """

    def __init__(self, player, map, font):
        """Initializes the renderer and loads all visual assets (wall, key, exit, monster)."""
        self.rays = []
        self.player = player
        self.map = map
        self.font = font
        self.z_buffer = [0 for _ in range(NUM_RAYS)]

        self.wall_texture = pygame.image.load(IMG_PATH + "wall.png").convert_alpha()
        self.wall_texture = pygame.transform.scale(self.wall_texture, (TEXTURE_SIZE, TEXTURE_SIZE))

        try:
            self.key_texture = pygame.image.load(IMG_PATH + "key.png").convert_alpha()
            self.key_texture = pygame.transform.scale(self.key_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.key_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            self.key_texture.fill((255, 215, 0))
            pygame.draw.circle(self.key_texture, (0, 0, 0), (32, 32), 10)

        try:
            self.exit_texture = pygame.image.load(IMG_PATH + "exit.png").convert_alpha()
            self.exit_texture = pygame.transform.scale(self.exit_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.exit_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            self.exit_texture.fill((0, 255, 255))
            pygame.draw.rect(self.exit_texture, (0, 0, 0), (16, 16, 32, 32), 2)

        # Energy Item Texture
        try:
            self.energy_item_texture = pygame.image.load(IMG_PATH + "energy.png").convert_alpha()
            self.energy_item_texture = pygame.transform.scale(self.energy_item_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.energy_item_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.energy_item_texture, (0, 100, 255), (32, 32), 20)
            pygame.draw.circle(self.energy_item_texture, (200, 230, 255), (32, 32), 10) # Shine effect

        # Health Item Texture
        try:
            self.health_item_texture = pygame.image.load(IMG_PATH + "health.png").convert_alpha()
            self.health_item_texture = pygame.transform.scale(self.health_item_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.health_item_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.health_item_texture, (220, 0, 0), (32, 32), 20)
            pygame.draw.rect(self.health_item_texture, (255, 255, 255), (28, 20, 8, 24))
            pygame.draw.rect(self.health_item_texture, (255, 255, 255), (20, 28, 24, 8))

        # Armor Item Texture
        try:
            self.armor_item_texture = pygame.image.load(IMG_PATH + "armor.png").convert_alpha()
            self.armor_item_texture = pygame.transform.scale(self.armor_item_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.armor_item_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(self.armor_item_texture, (150, 150, 150), (16, 16, 32, 32))
            pygame.draw.rect(self.armor_item_texture, (200, 200, 200), (20, 20, 24, 24), 2)

        # Spike Trap Texture
        self.spike_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.spike_texture, (100, 100, 100), (0, 48, 64, 16)) # Base
        for i in range(4):
            pygame.draw.polygon(self.spike_texture, (150, 150, 150), [(i*16+4, 48), (i*16+8, 32), (i*16+12, 48)])

        self.spike_triggered_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.spike_triggered_texture, (100, 100, 100), (0, 48, 64, 16))
        for i in range(4):
            pygame.draw.polygon(self.spike_triggered_texture, (200, 200, 200), [(i*16+4, 48), (i*16+8, 10), (i*16+12, 48)])

        # Mimic Texture (looks like a chest/key)
        self.mimic_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(self.mimic_texture, (139, 69, 19), (12, 20, 40, 30))
        pygame.draw.rect(self.mimic_texture, (255, 215, 0), (28, 35, 8, 10))

        try:
            self.monster_texture = pygame.image.load(IMG_PATH + "monster.png").convert_alpha()
            self.monster_texture = pygame.transform.scale(self.monster_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except Exception as e:
            self.monster_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.monster_texture, (255, 255, 0), (32, 32), 20)

        # Load Floor Texture
        try:
            self.floor_texture = pygame.image.load(IMG_PATH + "floor.png").convert_alpha()
            self.floor_texture = pygame.transform.scale(self.floor_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.floor_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            self.floor_texture.fill((40, 40, 40)) # Màu nền sàn
            # Tự vẽ hoa văn sàn (Ví dụ: gạch caro)
            pygame.draw.rect(self.floor_texture, (50, 50, 50), (0, 0, TEXTURE_SIZE, TEXTURE_SIZE), 2)
            pygame.draw.line(self.floor_texture, (30, 30, 30), (0,0), (TEXTURE_SIZE, TEXTURE_SIZE), 1)
        
        # Load Ceiling Texture
        try:
            self.ceiling_texture = pygame.image.load(IMG_PATH + "ceiling.png").convert_alpha()
            self.ceiling_texture = pygame.transform.scale(self.ceiling_texture, (TEXTURE_SIZE, TEXTURE_SIZE))
        except:
            self.ceiling_texture = pygame.Surface((TEXTURE_SIZE, TEXTURE_SIZE))
            self.ceiling_texture.fill((20, 20, 25)) 
            for _ in range(10):
                rx, ry = random.randint(0, TEXTURE_SIZE), random.randint(0, TEXTURE_SIZE)
                pygame.draw.circle(self.ceiling_texture, (40, 40, 50), (rx, ry), 2)
                
        # --- NEW: PARALLAX SKY TEXTURE ---
        self.sky_texture = pygame.Surface((WINDOW_WIDTH * 2, WINDOW_HEIGHT // 2))
        self.sky_texture.fill((10, 10, 20)) # Dark night sky
        # Draw some stars
        for _ in range(150):
            sx, sy = random.randint(0, WINDOW_WIDTH * 2), random.randint(0, WINDOW_HEIGHT // 2)
            pygame.draw.circle(self.sky_texture, (200, 200, 255), (sx, sy), random.randint(1, 2))
        # Draw a distant mountain or glow
        pygame.draw.ellipse(self.sky_texture, (20, 20, 40), (-100, WINDOW_HEIGHT // 4, WINDOW_WIDTH * 2 + 200, WINDOW_HEIGHT // 2))

    def castAllRays(self):
        """Casts all rays across the FOV and stores distances in the z_buffer."""
        self.rays = []
        rayAngle = self.player.rotationAngle - FOV / 2
        for i in range(NUM_RAYS):
            ray = Ray(rayAngle, self.player, self.map)
            ray.cast()
            self.rays.append(ray)
            dist = ray.distance * math.cos(rayAngle - self.player.rotationAngle)
            self.z_buffer[i] = dist if dist > 0 else 0.1
            rayAngle += FOV / NUM_RAYS

    def renderSprites(self, screen, sprites):
        """
        Renders all game entities (Monsters, Key, Exit).
        Sorts entities by distance to handle proper depth overlapping.
        """
        for sprite in sprites:
            if not sprite.alive: continue
            dx = sprite.x - self.player.x
            dy = sprite.y - self.player.y
            sprite.dist = math.sqrt(dx**2 + dy**2)
            sprite_angle = math.atan2(dy, dx) - self.player.rotationAngle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            sprite.angle = sprite_angle

        sprites.sort(key=lambda s: s.dist if hasattr(s, 'dist') else 0, reverse=True)

        for sprite in sprites:
            if not sprite.alive: continue
            if abs(sprite.angle) < FOV:
                screen_x = (0.5 * (sprite.angle / (FOV / 2)) + 0.5) * WINDOW_WIDTH
                sprite_height = (WALL_HEIGHT / (sprite.dist if sprite.dist > 0.1 else 0.1)) * 415
                sprite_width = sprite_height
                
                active_tex = self.monster_texture
                is_monster = True
                v_offset = 0
                if hasattr(sprite, 'type'):
                    is_monster = False
                    if hasattr(sprite, 'update_animation'):
                        sprite.update_animation()
                        # Only apply offset for the initial drop "pop-up" effect
                        if sprite.dropped and sprite.drop_timer > 0:
                            v_offset = -(sprite.drop_timer / 30) * 40

                    if sprite.type == 'key': active_tex = self.key_texture
                    elif sprite.type == 'exit': active_tex = self.exit_texture
                    elif sprite.type == 'energy': active_tex = self.energy_item_texture
                    elif sprite.type == 'health': active_tex = self.health_item_texture
                    elif sprite.type == 'armor': active_tex = self.armor_item_texture
                    elif sprite.type == 'spike':
                        active_tex = self.spike_triggered_texture if sprite.triggered else self.spike_texture
                    elif sprite.type == 'mimic':
                        active_tex = self.mimic_texture

                draw_y = (WINDOW_HEIGHT / 2) - (sprite_height / 2) + v_offset
                start_x = int(screen_x - sprite_width / 2)
                end_x = int(screen_x + sprite_width / 2)

                sprite_visible = False
                for x in range(start_x, end_x, RES):
                    col_idx = x // RES
                    if 0 <= col_idx < NUM_RAYS:
                        if sprite.dist < self.z_buffer[col_idx]:    
                            sprite_visible = True
                            tex_x = int((x - start_x) / sprite_width * TEXTURE_SIZE)
                            if 0 <= tex_x < TEXTURE_SIZE:
                                try:
                                    sprite_col = pygame.transform.scale(active_tex.subsurface(tex_x, 0, 1, TEXTURE_SIZE), (RES, int(sprite_height)))
                                    # Use the same fog logic for sprites
                                    fog_max_dist = 400
                                    fog_factor = max(0.1, min(1.0, (fog_max_dist - sprite.dist) / fog_max_dist))
                                    shading = (fog_factor ** 1.5) * self.player.torch_intensity
                                    sprite_col.fill((shading*255, shading*255, shading*255), special_flags=pygame.BLEND_RGB_MULT)       
                                    screen.blit(sprite_col, (x, draw_y))
                                except: pass

                if is_monster and sprite_visible:
                    bar_width, bar_height = sprite_width / 2, 5
                    bar_x, bar_y = screen_x - bar_width / 2, draw_y - 10
                    if 0 <= bar_x < WINDOW_WIDTH:
                        pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))
                        hp_percent = max(0, sprite.hp / 30)
                        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width * hp_percent, bar_height))
                        hp_text = self.font.render(f"{int(sprite.hp)}", True, (255, 255, 255))
                        screen.blit(hp_text, (bar_x, bar_y - 20))   

    def render(self, screen, sprites=None):
        """
        Executes the full 3D rendering pipeline.
        Optimized for performance and true fog effect.
        """
        # --- PARALLAX SKY ---
        # Calculate offset based on player rotation
        sky_offset = -int((self.player.rotationAngle % (2 * math.pi)) / (2 * math.pi) * WINDOW_WIDTH)
        screen.blit(self.sky_texture, (sky_offset, 0))
        screen.blit(self.sky_texture, (sky_offset + WINDOW_WIDTH, 0))
        screen.blit(self.sky_texture, (sky_offset - WINDOW_WIDTH, 0))

        # Draw floor with a gradient to horizon
        for y in range(WINDOW_HEIGHT // 2, WINDOW_HEIGHT, 8):
            f_shading = max(5, min(60, (y - WINDOW_HEIGHT // 2) / (WINDOW_HEIGHT // 2) * 80))
            pygame.draw.rect(screen, (f_shading, f_shading, f_shading + 10), (0, y, WINDOW_WIDTH, 8))

        i = 0
        for ray in self.rays:
            # Distance correction to prevent fisheye
            corrected_dist = ray.distance * math.cos(ray.rayAngle - self.player.rotationAngle)
            self.z_buffer[i] = corrected_dist
            
            line_height = (WALL_HEIGHT / (corrected_dist if corrected_dist > 0.1 else 0.1)) * 415    
            draw_begin = (WINDOW_HEIGHT / 2) - (line_height / 2) + self.player.bob_offset 
            
            tex_x = int(ray.wall_offset * (TEXTURE_SIZE - 1))       
            
            active_tex = self.wall_texture
                
            wall_column = active_tex.subsurface(tex_x, 0, 1, TEXTURE_SIZE)
            wall_column = pygame.transform.scale(wall_column, (RES, int(line_height)))
            
            # --- IMPROVED FOG EFFECT ---
            # Linear fog with torch influence
            fog_max_dist = 400
            fog_factor = max(0.0, min(1.0, (fog_max_dist - corrected_dist) / fog_max_dist))
            
            final_shading = (fog_factor ** 1.5) * self.player.torch_intensity
            
            if ray.was_hit_vertical: final_shading *= 0.8 # Simulating directional light
            
            color_val = max(10, min(250, int(final_shading * 255)))
            wall_column.fill((color_val, color_val, color_val + 5), special_flags=pygame.BLEND_RGB_MULT)
            screen.blit(wall_column, (i * RES, draw_begin))
            i += 1
            
        if sprites:
            self.renderSprites(screen, sprites)
