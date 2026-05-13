import pygame
import math
import random
from settings import *

class Player:
    """
    Represents the player in the 3D space.
    Manages kinematic parameters including position (x, y), rotation angle,
    and handles input from keyboard and mouse.
    """

    def __init__(self, map, font):
        """Initializes the player at the screen center with default stats."""
        self.x = WINDOW_WIDTH / 2
        self.y = WINDOW_HEIGHT / 2
        self.radius = 5
        self.map = map
        self.font = font

        self.turnDirection = 0
        self.walkDirection = 0
        self.rotationAngle = 0
        self.moveSpeed = 2.5
        self.rotationSpeed = 2 * (math.pi / 180)

        self.hp = 100
        self.armor = 0
        self.max_armor = 100
        self.energy = 100
        self.max_energy = 100
        self.is_shooting = False
        self.shoot_timer = 0
        self.has_key = False
        self.win = False
        
        self.inventory = []
        self.show_inventory = False
        self.damage_timer = 0
        
        # Environmental effects
        self.walk_timer = 0
        self.bob_offset = 0
        self.torch_intensity = 1.0
        self.torch_timer = 0
        
        # Weapon Animation
        self.weapon_sway = 0
        self.weapon_recoil = 0
        self.last_footstep_time = 0

    def take_damage(self, amount):
        """Reduces player HP when attacked, considering armor."""
        if self.armor > 0:
            reduction = min(self.armor, amount * 0.5) # Armor absorbs 50% of damage
            self.armor -= reduction
            amount -= reduction
        
        self.hp -= amount
        if self.hp < 0: self.hp = 0
        self.damage_timer = 10 # Show red flash for 10 frames

    def shoot(self, monsters, qtree=None, items_list=None):
        """Handles shooting logic, consumes energy, and ensures only the closest visible monster is hit."""
        if self.energy < 2: return # Need at least 2 energy to shoot

        self.is_shooting = True
        self.shoot_timer = 6 
        self.energy -= 2 # Consume energy
        self.weapon_recoil = 15 # Start recoil effect

        target_monster = None
        min_dist = 200

        # USE QUADTREE FOR OPTIMIZED SEARCH
        if qtree:
            from quadtree import Rect
            search_range = Rect(self.x, self.y, 200, 200)
            potential_targets = qtree.query(search_range)
            targets = [p.data for p in potential_targets if hasattr(p.data, 'hp')] # Only monsters have HP
        else:
            targets = monsters

        for monster in targets:
            if not monster.alive: continue

            dx = monster.x - self.x
            dy = monster.y - self.y
            dist = math.sqrt(dx**2 + dy**2)

            if dist < min_dist:
                angle_to_monster = math.atan2(dy, dx)
                angle_diff = angle_to_monster - self.rotationAngle      

                while angle_diff > math.pi: angle_diff -= 2 * math.pi   
                while angle_diff < -math.pi: angle_diff += 2 * math.pi  

                if abs(angle_diff) < 0.15: # Narrower field of fire
                    if not self.map.has_wall_between(self.x, self.y, monster.x, monster.y):
                        target_monster = monster
                        min_dist = dist
        
        if target_monster:
            target_monster.take_damage(10, items_list)

    def use_item(self, item_type):
        """Manually use an item from the inventory."""
        if item_type in self.inventory:
            if item_type == 'energy':
                self.energy = min(self.max_energy, self.energy + 30)
                self.inventory.remove('energy')
            elif item_type == 'health':
                self.hp = min(100, self.hp + 25)
                self.inventory.remove('health')
            return True
        return False

    def update(self, monsters=[], items=[], qtree=None, sounds={}):
        """Updates player position, angle, and handles interaction with items/monsters."""
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        self.turnDirection = 0
        self.walkDirection = 0
        if keys[pygame.K_RIGHT]:
            self.turnDirection = 1
        if keys[pygame.K_LEFT]:
            self.turnDirection = -1
        if keys[pygame.K_UP]:
            self.walkDirection = 1
        if keys[pygame.K_DOWN]:
            self.walkDirection = -1

        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
            self.is_shooting = False
            
        if self.damage_timer > 0:
            self.damage_timer -= 1

        # Update Weapon Recoil
        if self.weapon_recoil > 0:
            self.weapon_recoil -= 2
        else:
            self.weapon_recoil = 0

        moveStep = self.walkDirection * self.moveSpeed
        self.rotationAngle += self.turnDirection * self.rotationSpeed

        dx = math.cos(self.rotationAngle) * moveStep
        dy = math.sin(self.rotationAngle) * moveStep

        margin = 5 if self.walkDirection > 0 else -5

        # --- OPTIMIZED COLLISION DETECTION WITH QUADTREE ---
        nearby_entities = []
        if qtree:
            from quadtree import Rect
            search_range = Rect(self.x, self.y, 50, 50) # Check 50px around player
            points = qtree.query(search_range)
            nearby_entities = [p.data for p in points]
        else:
            nearby_entities = monsters

        can_move_x = True
        for entity in nearby_entities:
            if hasattr(entity, 'hp'): # It's a Monster
                if not entity.alive: continue
                if math.sqrt((self.x + dx - entity.x)**2 + (self.y - entity.y)**2) < self.radius + entity.radius + 2:
                    can_move_x = False
                    break

        if can_move_x:
            new_x_grid = int((self.x + dx + (margin * math.cos(self.rotationAngle))) / TILESIZE)
            current_y_grid = int(self.y / TILESIZE)
            if 0 <= new_x_grid < COLS and self.map.grid[current_y_grid][new_x_grid] == 0:
                self.x += dx

        can_move_y = True
        for entity in nearby_entities:
            if hasattr(entity, 'hp'): # It's a Monster
                if not entity.alive: continue
                if math.sqrt((self.x - entity.x)**2 + (self.y + dy - entity.y)**2) < self.radius + entity.radius + 2:
                    can_move_y = False
                    break

        if can_move_y:
            new_y_grid = int((self.y + dy + (margin * math.sin(self.rotationAngle))) / TILESIZE)
            current_x_grid = int(self.x / TILESIZE)
            if 0 <= new_y_grid < ROWS and self.map.grid[new_y_grid][current_x_grid] == 0:
                self.y += dy
        
        # Calculate Head Bobbing and Play Footsteps
        if self.walkDirection != 0 or self.turnDirection != 0:
            self.walk_timer += 0.2
            self.bob_offset = math.sin(self.walk_timer) * 4
            
            # Play Footstep Sound
            if self.walkDirection != 0 and current_time - self.last_footstep_time > FOOTSTEP_INTERVAL:
                if 'footstep' in sounds:
                    sounds['footstep'].play()
                    self.last_footstep_time = current_time
        else:
            self.walk_timer = 0
            self.bob_offset = 0
            
        # Calculate Torch Flicker
        self.torch_timer += 0.05
        self.torch_intensity = 0.95 + math.sin(self.torch_timer * 4) * 0.05 + random.random() * 0.02

        if keys[pygame.K_RETURN]:
            interact_range = TILESIZE
            
            front_x = self.x + math.cos(self.rotationAngle) * interact_range
            front_y = self.y + math.sin(self.rotationAngle) * interact_range
            grid_x = int(front_x / TILESIZE)
            grid_y = int(front_y / TILESIZE)
            
            if 0 <= grid_x < COLS and 0 <= grid_y < ROWS:
                if self.map.grid[grid_y][grid_x] == 4:
                    if self.has_key:
                        self.map.grid[grid_y][grid_x] = 0
            
            # --- OPTIMIZED ITEM INTERACTION ---
            targets = nearby_entities if qtree else items
            for item in targets:
                if not hasattr(item, 'type') or not item.alive: continue
                dist = math.sqrt((self.x - item.x)**2 + (self.y - item.y)**2)
                if dist < interact_range:
                    if 'pickup' in sounds: sounds['pickup'].play()
                    if item.type == 'key':
                        self.has_key = True
                        item.alive = False
                    elif item.type == 'exit' and self.has_key:
                        self.win = True
                    elif item.type == 'armor':
                        self.armor = min(self.max_armor, self.armor + 25)
                        item.alive = False
                    elif item.type in ['energy', 'health']:
                        # Manual collection for manual use
                        self.inventory.append(item.type)
                        item.alive = False
                    
                    if item.alive == False and item.type == 'key':
                        self.inventory.append(item.type)

    def render_ui(self, screen, elapsed_time):
        """Renders the player HUD (HP, Energy, Key status, Radar)."""
        # --- DRAW TIMER ---
        timer_text = self.font.render(f"TIME: {elapsed_time:.2f}s", True, (255, 255, 255))
        screen.blit(timer_text, (WINDOW_WIDTH // 2 - 50, 20))

        # Damage Flash
        if self.damage_timer > 0:
            damage_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            damage_surf.set_alpha(100)
            damage_surf.fill((255, 0, 0))
            screen.blit(damage_surf, (0, 0))

        ui_y = WINDOW_HEIGHT - 110
        # HP Bar
        pygame.draw.rect(screen, (50, 0, 0), (20, ui_y, 200, 15))   
        pygame.draw.rect(screen, (0, 255, 0), (20, ui_y, self.hp * 2, 15))
        hp_text = self.font.render(f"HP: {int(self.hp)}", True, (255, 255, 255))
        screen.blit(hp_text, (20, ui_y - 20))

        # Armor Bar
        ui_y += 35
        pygame.draw.rect(screen, (30, 30, 30), (20, ui_y, 200, 10))   
        pygame.draw.rect(screen, (150, 150, 150), (20, ui_y, self.armor * 2, 10))
        armor_text = self.font.render(f"ARMOR: {int(self.armor)}", True, (200, 200, 200))
        screen.blit(armor_text, (20, ui_y - 18))

        # Energy Bar
        ui_y += 30
        pygame.draw.rect(screen, (0, 0, 50), (20, ui_y, 200, 15))   
        pygame.draw.rect(screen, (0, 150, 255), (20, ui_y, self.energy * 2, 15))
        energy_text = self.font.render(f"ENERGY: {int(self.energy)}", True, (255, 255, 255))
        screen.blit(energy_text, (20, ui_y - 20))

        # --- INVENTORY UI ---
        if self.show_inventory:
            inv_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 200, 300, 400)
            pygame.draw.rect(screen, (30, 30, 30), inv_rect)
            pygame.draw.rect(screen, (200, 200, 200), inv_rect, 2)
            
            title = self.font.render("INVENTORY (TAB to close)", True, (255, 255, 255))
            screen.blit(title, (inv_rect.x + 20, inv_rect.y + 20))
            
            item_counts = {}
            for item in self.inventory:
                item_counts[item] = item_counts.get(item, 0) + 1
            
            for i, (item, count) in enumerate(item_counts.items()):
                item_text = self.font.render(f"{item.capitalize()}: x{count}", True, (200, 200, 200))
                screen.blit(item_text, (inv_rect.x + 30, inv_rect.y + 60 + i * 30))

        key_color = (255, 255, 0) if self.has_key else (100, 100, 100)
        key_text = self.font.render("KEY: FOUND" if self.has_key else "KEY: MISSING", True, key_color)
        screen.blit(key_text, (WINDOW_WIDTH - 150, ui_y - 25))      

        if not self.has_key and self.map.key_pos:
            dist_to_key = math.sqrt((self.x - (self.map.key_pos[0] * TILESIZE + TILESIZE//2))**2 +
                                    (self.y - (self.map.key_pos[1] * TILESIZE + TILESIZE//2))**2)
            dist_text = self.font.render(f"Dist to Key: {int(dist_to_key / TILESIZE)}m", True, (255, 255, 0))
            screen.blit(dist_text, (WINDOW_WIDTH - 150, ui_y - 50)) 

        if self.map.exit_pos:
            dist_to_exit = math.sqrt((self.x - (self.map.exit_pos[0] * TILESIZE + TILESIZE//2))**2 +
                                     (self.y - (self.map.exit_pos[1] * TILESIZE + TILESIZE//2))**2)
            exit_text = self.font.render(f"Exit: {int(dist_to_exit / TILESIZE)}m", True, (0, 255, 255))
            screen.blit(exit_text, (WINDOW_WIDTH - 150, ui_y - 75)) 

        color = (255, 255, 255) if self.is_shooting else (200, 200, 200)
        
        # Draw a bright flash at the bottom or near the center
        if self.is_shooting:
            flash_size = random.randint(40, 60)
            pygame.draw.circle(screen, (255, 255, 200), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100), flash_size)
            
            # Simple Screen Flash
            flash_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            flash_surf.set_alpha(30)
            flash_surf.fill((255, 255, 255))
            screen.blit(flash_surf, (0, 0))

        # --- DRAW WEAPON HUD ---
        sway_x = math.sin(self.walk_timer) * 15 if self.walkDirection != 0 else 0
        sway_y = abs(math.cos(self.walk_timer) * 10) if self.walkDirection != 0 else 0
        
        weapon_x = WINDOW_WIDTH // 2 + sway_x
        weapon_y = WINDOW_HEIGHT - 180 + sway_y + self.weapon_recoil
        
        # Draw a simple procedural gun (Nòng súng)
        pygame.draw.rect(screen, (30, 30, 30), (weapon_x - 25, weapon_y, 50, 200)) # Thân súng
        pygame.draw.rect(screen, (20, 20, 20), (weapon_x - 15, weapon_y - 20, 30, 50)) # Đầu nòng
        pygame.draw.rect(screen, (50, 50, 50), (weapon_x - 5, weapon_y - 10, 10, 40)) # Chi tiết nòng
        
        # Crosshair
        pygame.draw.circle(screen, color, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), 5, 1)
        pygame.draw.line(screen, color, (WINDOW_WIDTH // 2 - 10, WINDOW_HEIGHT // 2), (WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT // 2), 1)  
        pygame.draw.line(screen, color, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 10), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10), 1)  

    def render_on_minimap(self, screen):
        """Renders the player icon on the Mini-map at the top-right."""
        scale = MINIMAP_SCALE
        offset_x = WINDOW_WIDTH - (COLS * TILESIZE * scale) - 10
        offset_y = 10
        
        px = offset_x + self.x * scale
        py = offset_y + self.y * scale
        
        pygame.draw.circle(screen, (255, 0, 0), (int(px), int(py)), 3)
        # Direction line
        pygame.draw.line(screen, (255, 255, 0), (px, py), 
                         (px + math.cos(self.rotationAngle) * 8, 
                          py + math.sin(self.rotationAngle) * 8), 2)

    def render(self, screen):
        """Renders player entity in 2D space (debugging)."""
        pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), self.radius)
        pygame.draw.line(screen, (255, 0, 0), (self.x,self.y), (self.x + math.cos(self.rotationAngle) * 50, self.y + math.sin(self.rotationAngle) * 50))
