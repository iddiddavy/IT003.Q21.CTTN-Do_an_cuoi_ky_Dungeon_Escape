"""
Module: settings.py
------------------
Stores all system configuration parameters and environment constants.
Includes: Screen dimensions, Field of View (FOV), movement speeds, ray resolution,
and paths for image/audio assets.
"""
import math

TILESIZE = 16

ROWS = 60
COLS = 80
WALL_HEIGHT = 16

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

MINIMAP_SCALE = 0.15
MINIMAP_TILESIZE = TILESIZE * MINIMAP_SCALE

TEXTURE_SIZE = 64

FOV = 60 * (math.pi / 180)

RES = 2
NUM_RAYS = WINDOW_WIDTH // RES

IMG_PATH = "C:/votranngocvy/DSA/Game/Project/Images/"

# Sound Settings
SOUND_PATH = "C:/votranngocvy/DSA/Game/Project/Sounds/"
FOOTSTEP_INTERVAL = 300 # ms between footstep sounds
GROWL_DISTANCE = 150 # Distance to trigger monster growl
GROWL_INTERVAL = 3000 # ms between growls
