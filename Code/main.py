import pygame
from settings import *
from map import Map
from player import Player
from raycaster import RayCaster
from entities import Monster, Item, Trap
from quadtree import QuadTree, Rect, Point
import random
import math
import sys

# Global variables for timing and records
start_ticks = 0
best_time = float('inf')

"""  
Module: main.py
--------------
Entry point for the application. Initializes Pygame, manages game states,
and executes the core Game Loop.
"""

def load_best_time():
    """Loads the best time from a file."""
    try:
        with open("C:/votranngocvy/DSA/Game/Project/best_time.txt", "r") as f:
            return float(f.read())
    except: return float('inf')

def save_best_time(time_val):
    """Saves the best time to a file."""
    try:
        with open("C:/votranngocvy/DSA/Game/Project/best_time.txt", "w") as f:
            f.write(str(time_val))
    except Exception as e:
        print(f"Error saving best time: {e}")

def reset_game():
    """Resets all game states (new map, player, and monsters)."""
    global game_map, player, monsters, items, traps, raycaster, game_over, num_monsters, spawn_cooldown, item_spawn_cooldown, font_ui, qtree, num_energy, start_ticks, best_time
    game_map = Map()
    spawn_x, spawn_y = game_map.get_spawn_pos()
    player = Player(game_map, font_ui)
    player.x, player.y = spawn_x, spawn_y
    
    start_ticks = pygame.time.get_ticks()
    best_time = load_best_time()

    monsters = []
    traps = []
    other_rooms = [room for room in game_map.all_rooms if room != game_map.spawn_room]
    
    # Spawn Traps
    num_traps = 15
    trap_rooms = random.sample(other_rooms, min(num_traps, len(other_rooms)))
    for room in trap_rooms:
        t_x, t_y = (room[0] + random.randint(1, room[2]-2)) * TILESIZE, (room[1] + random.randint(1, room[3]-2)) * TILESIZE
        trap_type = random.choice(['spike', 'mimic'])
        traps.append(Trap(t_x, t_y, trap_type, player))

    num_monsters = min(len(other_rooms), random.randint(8, 12))      
    selected_rooms = random.sample(other_rooms, num_monsters)       
    for room in selected_rooms:
        m_x, m_y = (room[0] + room[2] // 2) * TILESIZE, (room[1] + room[3] // 2) * TILESIZE
        monsters.append(Monster(m_x, m_y, game_map, player))        

    items = []
    if game_map.key_pos:
        items.append(Item(game_map.key_pos[0] * TILESIZE + TILESIZE // 2, game_map.key_pos[1] * TILESIZE + TILESIZE // 2, 'key'))
    if game_map.exit_pos:
        items.append(Item(game_map.exit_pos[0] * TILESIZE + TILESIZE // 2, game_map.exit_pos[1] * TILESIZE + TILESIZE // 2, 'exit'))

    # Spawn Initial Items
    num_energy = 15
    num_health = 10
    total_items = num_energy + num_health
    item_rooms = random.sample(other_rooms, min(total_items, len(other_rooms)))
    for i, room in enumerate(item_rooms):
        e_x, e_y = (room[0] + random.randint(1, room[2]-2)) * TILESIZE, (room[1] + random.randint(1, room[3]-2)) * TILESIZE
        itype = 'energy' if i < num_energy else 'health'
        items.append(Item(e_x, e_y, itype))

    raycaster = RayCaster(player, game_map, font_ui)
    game_over = False
    spawn_cooldown = 0
    item_spawn_cooldown = 0
    qtree = None

def draw_button(screen, font_button, text, y_pos, color=(200, 200, 200)):
    """Draws an interactive button on the menu screen."""
    text_surf = font_button.render(text, True, color)
    text_rect = text_surf.get_rect(center=(WINDOW_WIDTH // 2, y_pos))
    padding = 20
    button_rect = pygame.Rect(text_rect.left - padding, text_rect.top - 10, text_rect.width + padding*2, text_rect.height + 20)
    mouse_pos = pygame.mouse.get_pos()
    is_hover = button_rect.collidepoint(mouse_pos)

    if is_hover:
        pygame.draw.rect(screen, (100, 100, 100), button_rect)      
        if pygame.mouse.get_pressed()[0]: return True
    else: pygame.draw.rect(screen, (50, 50, 50), button_rect)

    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)       
    screen.blit(text_surf, text_rect)
    return False

def draw_menu(screen, font_title, font_button, img_title):
    """Displays the main Menu screen."""
    screen.fill((20, 20, 20))
    # Move title down to be more centered
    title_y = 200
    if img_title: screen.blit(img_title, img_title.get_rect(center=(WINDOW_WIDTH // 2, title_y)))
    else:
        title_surf = font_title.render("DUNGEON ESCAPE", True, (255, 215, 0))
        screen.blit(title_surf, title_surf.get_rect(center=(WINDOW_WIDTH // 2, title_y)))
    
    # Move buttons down accordingly
    if draw_button(screen, font_button, "PLAY GAME", 350):
        reset_game()
        return "PLAYING"
    if draw_button(screen, font_button, "INSTRUCTIONS", 430): 
        return "INSTRUCTIONS"
    return "MENU"

def draw_instructions(screen, font_ui, font_button):
    """Displays the gameplay instructions screen."""
    screen.fill((20, 20, 20))
    instr = ["CONTROLS:", "- ARROW KEYS: Move & Turn", "- SPACE: Shoot Monsters", "- ENTER: Pickup Key / Use Exit", "- TAB: Open/Close Inventory", "- 1: Use Health Potion", "- 2: Use Energy Potion", "", "OBJECTIVE:", "1. Find the GOLDEN KEY", "2. Reach the CYAN EXIT", "3. Survive!"]
    for i, line in enumerate(instr):
        text_surf = font_ui.render(line, True, (255, 255, 255))     
        screen.blit(text_surf, (100, 80 + i * 30))
    if draw_button(screen, font_button, "BACK TO MENU", 400): return "MENU"
    return "INSTRUCTIONS"

def main():
    """Main function to initialize and run and game."""
    global font_ui, current_state, game_over, spawn_cooldown, item_spawn_cooldown, qtree, num_energy, start_ticks, best_time
    
    pygame.init()
    pygame.mixer.init() # Initialize sound mixer
    pygame.font.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))     
    pygame.display.set_caption("Dungeon Escape")

    # LOAD ASSETS
    try:
        img_title = pygame.image.load(IMG_PATH + "title.png").convert_alpha()
    except:
        img_title = None

    # LOAD SOUNDS
    sounds = {}
    try:
        pygame.mixer.music.load(SOUND_PATH + "dungeon_music.mp3")
        pygame.mixer.music.set_volume(0.5)
    except:
        print("Sound files not found in", SOUND_PATH)

    font_title = pygame.font.SysFont('Arial', 64, bold=True)
    font_button = pygame.font.SysFont('Arial', 32)
    font_ui = pygame.font.SysFont('Arial', 18)

    current_state = "MENU"
    reset_game()
    clock = pygame.time.Clock()
    music_playing = False
    last_growl_time = 0

    while True:
        clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                sys.exit()
            if current_state == "PLAYING" and not game_over:        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: 
                        player.shoot(monsters, qtree, items)
                        if 'shoot' in sounds: sounds['shoot'].play()
                    if event.key == pygame.K_TAB:
                        player.show_inventory = not player.show_inventory
                    if event.key == pygame.K_1:
                        player.use_item('health')
                    if event.key == pygame.K_2:
                        player.use_item('energy')

        if current_state == "MENU": 
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                music_playing = False
            current_state = draw_menu(screen, font_title, font_button, img_title)
        elif current_state == "INSTRUCTIONS": 
            current_state = draw_instructions(screen, font_ui, font_button)
        elif current_state == "PLAYING":
            if not music_playing:
                try:
                    pygame.mixer.music.play(-1) # Loop forever
                    music_playing = True
                except: pass

            if not game_over:
                # REBUILD QUADTREE
                boundary = Rect((COLS * TILESIZE) / 2, (ROWS * TILESIZE) / 2, (COLS * TILESIZE) / 2, (ROWS * TILESIZE) / 2)
                qtree = QuadTree(boundary, 4)
                for m in monsters: qtree.insert(Point(m.x, m.y, m))
                for it in items: qtree.insert(Point(it.x, it.y, it))
                for t in traps: qtree.insert(Point(t.x, t.y, t))

                player.update(monsters, items, qtree, sounds)
                
                # Monster Proximity Growl
                closest_dist = float('inf')
                for monster in monsters: 
                    monster.update(qtree)
                    dist = math.sqrt((monster.x - player.x)**2 + (monster.y - player.y)**2)
                    if dist < closest_dist: closest_dist = dist
                
                if closest_dist < GROWL_DISTANCE and current_time - last_growl_time > GROWL_INTERVAL:
                    if 'growl' in sounds:
                        sounds['growl'].set_volume(1.0 - (closest_dist / GROWL_DISTANCE))
                        sounds['growl'].play()
                        last_growl_time = current_time
                
                # Update Traps
                for trap in traps:
                    result = trap.update()
                    if result == 'transform':
                        monsters.append(Monster(trap.x, trap.y, game_map, player))
                
                # Global monsters and items are updated here
                globals()['monsters'] = [m for m in monsters if m.alive]
                globals()['items'] = [item for item in items if item.alive]
                globals()['traps'] = [t for t in traps if t.alive]

                if len(monsters) < num_monsters:
                    spawn_cooldown += 1
                    if spawn_cooldown > 300:
                        target_room = random.choice(game_map.all_rooms) 
                        m_x, m_y = (target_room[0] + target_room[2] // 2) * TILESIZE, (target_room[1] + target_room[3] // 2) * TILESIZE
                        if math.sqrt((m_x - player.x)**2 + (m_y - player.y)**2) > 150:
                            monsters.append(Monster(m_x, m_y, game_map, player))
                            spawn_cooldown = 0
                
                # ITEM DYNAMIC SPAWNING
                energy_items_count = len([it for it in items if it.type == 'energy'])
                health_items_count = len([it for it in items if it.type == 'health'])
                if energy_items_count < 15 or health_items_count < 10:
                    item_spawn_cooldown += 1
                    if item_spawn_cooldown > 450:
                        target_room = random.choice(game_map.all_rooms)
                        e_x, e_y = (target_room[0] + random.randint(1, target_room[2]-2)) * TILESIZE, (target_room[1] + random.randint(1, target_room[3]-2)) * TILESIZE
                        itype = 'energy' if energy_items_count < 15 else 'health'
                        items.append(Item(e_x, e_y, itype))
                        item_spawn_cooldown = 0

                raycaster.castAllRays()

            screen.fill((0,0,0))
            raycaster.render(screen, monsters + items + traps)
            
            elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000
            player.render_ui(screen, elapsed_time)
            game_map.render_minimap(screen)
            
            # OPTIONAL: Visualizing Quadtree on minimap (for debug/showcase)
            # qtree.render(screen, MINIMAP_SCALE)
            
            player.render_on_minimap(screen)
            for monster in monsters: monster.render_on_minimap(screen)

            if player.hp <= 0 or player.win:
                if not game_over: # First frame of game over
                    final_time = (pygame.time.get_ticks() - start_ticks) / 1000
                    if player.win and final_time < best_time:
                        best_time = final_time
                        save_best_time(best_time)
                    game_over = True

                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0,0))
                
                msg = "GAME OVER" if player.hp <= 0 else "YOU WIN!"
                color = (255, 0, 0) if player.hp <= 0 else (0, 255, 0)
                text = font_title.render(msg, True, color)
                screen.blit(text, text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 150)))
                
                if player.win:
                    time_text = font_button.render(f"Your Time: {final_time:.2f}s", True, (255, 255, 255))
                    screen.blit(time_text, time_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)))
                    
                    best_txt = f"Best Time: {best_time:.2f}s" if best_time != float('inf') else "Best Time: --"
                    best_text = font_button.render(best_txt, True, (255, 215, 0))
                    screen.blit(best_text, best_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))

                if draw_button(screen, font_button, "PLAY AGAIN", WINDOW_HEIGHT // 2 + 60, (200, 200, 200)):
                    reset_game()
                    game_over = False
                if draw_button(screen, font_button, "MAIN MENU", WINDOW_HEIGHT // 2 + 140, (200, 200, 200)):
                    current_state = "MENU"
                    game_over = False
        
        pygame.display.update()

if __name__ == "__main__":
    main()
