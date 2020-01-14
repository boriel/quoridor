# -*- coding: utf-8 -*-

import os
from pygame import Color

from entities.coord import Coord

__doc__ = """ Centralizes all global configuration flags """

# Debug FLAG
__DEBUG__ = False

# Frame rate
FRAMERATE = 25

# Config Options
GAME_TITLE = 'Quoridor'
DEFAULT_NUM_PLAYERS = 2

# Cell size
CELL_WIDTH = 50
CELL_HEIGHT = 50
CELL_PAD = 7
CELL_BORDER_SIZE = 2

# Default Number of rows and cols
DEF_ROWS = 9
DEF_COLS = 9

# Number of Walls per player
NUM_WALLS = 10

### COLORS ###
# Font Color & SIZE
FONT_COLOR = Color(0, 10, 50)
FONT_BG_COLOR = Color(255, 255, 255)
FONT_SIZE = 16

# Board Background and Border color and look
BOARD_BG_COLOR = Color(240, 255, 255)
BOARD_BRD_COLOR = Color(0, 0, 40)
BOARD_BRD_SIZE = 1

# Cell colors
CELL_BORDER_COLOR = Color(40, 40, 40)
CELL_COLOR = Color(120, 90, 60)
CELL_VALID_COLOR = Color(40, 120, 120)  # Cyan

# Wall Color
WALL_COLOR = Color(10, 10, 10)

# Pawns color
PAWN_A_COL = Color(158, 60, 60)  # Red
PAWN_B_COL = Color(60, 60, 158)  # Blue
PAWN_BORDER_COL = Color(188, 188, 80)  # Yellow

# Gauge bars
GAUGE_WIDTH = CELL_WIDTH
GAUGE_HEIGHT = 5
GAUGE_COLOR = Color(128, 40, 40)
GAUGE_BORDER_COLOR = Color(0, 0, 0)

# Other constants
PAWN_PADDING = 25  # Pixels right to the board


class DIR:
    """ Directions
    """
    N = 0
    S = 1
    E = 2
    W = 3


DIRS = {DIR.N, DIR.S, DIR.E, DIR.W}  # Available directions
OPPOSITE_DIRS = [DIR.S, DIR.N, DIR.W, DIR.E]  # Reverse direction

# Delta to add to position to move into that direction
DIRS_DELTA = [Coord(-1, 0), Coord(+1, 0), Coord(0, -1), Coord(0, +1)]

# Network port
NETWORK_ENABLED = False  # Set to true to enable network playing
PORT = 8001  # This client port
BASE_PORT = 8000
SERVER_ADDR = 'localhost'
SERVER_URL = 'http://{}:{}'.format(SERVER_ADDR, PORT)

# Default AI playing level
LEVEL = 0

# Infinite
INF = 99

# Cache
CACHE_ENABLED = False
CACHE_DIR = './__cache'
CACHE_AI_FNAME = os.path.join(CACHE_DIR, 'ai.memo')
CACHE_DIST_FNAME = os.path.join(CACHE_DIR, 'dist.memo')
