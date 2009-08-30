#!/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pygame
from pygame.locals import *
from pygame import Color
from pygame import Rect
import copy
import re
import threading
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SocketServer import ThreadingMixIn
import xmlrpclib
import time

try:
    import psyco
except ImportError:
    pass


# Debug FLAG
__DEBUG__ = True

# Frame rate
FRAMERATE = 25

# Config Options
GAME_TITLE = 'Quoridor'
DEFAULT_NUM_PLAYERS = 2

# Cell size
CELL_WIDTH = 50
CELL_HEIGHT = 50
CELL_PAD = 5
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
CELL_VALID_COLOR = Color(40, 120, 120) # Cyan

# Wall Color
WALL_COLOR = Color(10, 10, 10)

# Pawns color
PAWN_A_COL = Color(158, 60, 60) # Red
PAWN_B_COL = Color(60, 60, 158) # Blue
PAWN_BORDER_COL = Color(188, 188, 80) # Yellow

# Other constants
PAWN_PADDING = 25 # Pixels right to the board

# Avaiable directions
dirs = ['N', 'S', 'E', 'W']
dirs_delta = {'N': (-1, 0), 'S': (+1, 0), 'E': (0, -1), 'W': (0, +1)}
opposite_dirs = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}

# This global counter counts the total number of players
# PAWNS instances uses it
PAWNS = 0

# Memoized put-wall cache
MEMOIZED_WALLS = {}

# --- Statistics ---
MEMOIZED_NODES = 0 # Memoized AI Nodes
MEMOIZED_NODES_HITS = 0 # Memoized Cache hits

# Network port
PORT = 8001
BASE_PORT = 8000
SERVER_URL = 'http://localhost'


def REPORT(msg):
    print msg



class EnhancedServer(ThreadingMixIn, SimpleXMLRPCServer):
    ''' Enhanced XML-RPC Server with some extended/overloaded functions.
    '''
    def serve_forever(self):
        self.quit = False
        self.encoding = 'utf-8'

        while not self.quit:
            self.handle_request()


    def terminate(self):
        self.quit = True


    def start(self):
        REPORT('Starting server')
        self.thread = threading.Thread(target = self.serve_forever)
        self.thread.start()
        REPORT('Done')


    def __del__(self):
        self.terminate()



def is_server_already_running():
	server = xmlrpclib.Server('http://localhost:%i' % PORT, allow_none = True, encoding = 'utf-8')
	try:
		return server.alive()
	except:
		pass

	return False




class Drawable(object):
    ''' Abstract drawable class
    '''
    def __init__(self, color = None,
                    border_color = None,
                    border_size = None):
        self.color = color
        self.border_color = border_color
        self.border_size = border_size

    def draw(self):
        if self.color is None or self.border_color is None:
            return

        if self.border_size is None:
            return

        r = self.rect
        if r is None:
            return

        pygame.draw.rect(screen, self.color, r, 0)
        pygame.draw.rect(screen, self.border_color, r, self.border_size)

    @property
    def rect(self):
        ''' Must be overloaded by children classes
        '''
        return None


class Pawn(Drawable):
    ''' Class defining a player pawn
    '''
    def __init__(self, board, color,
            border_color = PAWN_BORDER_COL,
            row = None,
            col = None,
            walls = NUM_WALLS,
            width = CELL_WIDTH - CELL_PAD,
            height = CELL_HEIGHT - CELL_PAD, # Set to True so the computer moves this pawn
            URL = None # Set
            ):
        global PAWNS

        self.color = color
        self.border_color = border_color
        self.width = width
        self.height = height
        self.i = row
        self.j = col
        self.board = board
        self.walls = walls # Walls per player
        self.__cell = None
        self.set_goal()
        self.id = PAWNS
        self.distances = DistArray(self)
        self.AI = None

        if URL is not None:
            REPORT('Connecting to server [%s]' % URL)

            count = 0
            maxtries = 10
            while count < maxtries:
                count += 1
                try:
                    NETWORK = xmlrpclib.Server(URL, \
                        allow_none = True, encoding = 'utf-8')
                    REPORT('Pinging server...')
                    if NETWORK.alive():
                        REPORT('Done!')
                        break
                except ValueError:
                    REPORT('Waiting for server...')
                    time.sleep(1.5)

            REPORT('Connected!')
            self.NETWORK = NETWORK
        else:
            self.NETWORK = None

        PAWNS += 1



    def __set_cell(self, cell):
        if self.__cell is not None: # Remove old cell if any
            self.__cell.pawn = None

        self.__cell = cell

        if cell is not None:
            self.__cell.pawn = self


    def __get_cell(self):
        row, col = (self.i, self.j)
        if row is None and col is None:
            return None

        return self.board[row][col]

    cell = property(__get_cell, __set_cell)


    def set_goal(self):
        ''' Sets a list of possible goals (cells) for this
        player.
        '''
        if self.i == 0:
            self.goals = [(self.board.rows - 1, x) for x in range(self.board.cols)]
        elif self.i == self.board.rows - 1:
            self.goals = [(0, x) for x in range(self.board.cols)]
        elif self.j == self.board.cols - 1:
            self.goals = [(x, 0) for x in range(self.board.cols)]
        else:
            self.goals = [(x, self.board.cols - 1) for x in range(self.board.rows)]


    def draw(self, r = None):
        if self.i is None or self.j is None:
            return

        if r is None:
            r = self.rect

        pygame.draw.ellipse(self.board.screen, self.color, r, 0)
        pygame.draw.ellipse(self.board.screen, self.border_color, r, 2)


    @property
    def rect(self):
        return self.board[self.i][self.j].rect


    def can_go(self, direction):
        ''' One of 'N', 'S', 'W', 'W'
        Returns False if can't go in that direction. Otherwise, returns
        a list of possible coordinates.
        '''
        if self.cell is None:
            return False # Uninitalized

        d = direction.upper()
        if d not in dirs:
            return False  # Unknown move

        if self.cell.path[d] is False:
            return False # Blocked in that direction

        I, J = dirs_delta[d]
        I += self.i
        J += self.j

        if not self.board.in_range(I, J):
            return False

        if self.board[I][J].pawn is None: # Is it free?
            return [(I, J)]

        # Ok there's a pawn at I, J. Check for adjacent
        result = []

        for di in dirs: # Check for any direction
            if di == opposite_dirs[d]:
                continue

            if self.board[I][J].path[di]:
                Ia, Ja = dirs_delta[di]
                Ia += I
                Ja += J

                if not self.board.in_range(Ia, Ja):
                    continue

                if self.board[Ia][Ja].pawn is None:
                    result += [(Ia, Ja)]

        return result


    @property
    def valid_moves(self):
        ''' Returns a list of valid moves as a tuples of (row, col)
        coordinates'''
        result = []

        if self.cell is None:
            return result

        for d in dirs: # Try each direction
            coords = self.can_go(d)
            if coords:
                result += coords

        return result



    def valid_moves_from(self, i, j):
        ''' Returns a list of valid moves from (i, j).
        (i, j) can be a different position from the
        current one.
        '''
        y = self.i
        x = self.j
        self.i = i
        self.j = j
        result = self.valid_moves
        self.i = y
        self.j = x

        return result


    def can_move(self, i, j):
        ''' Returns whether the pawn can move to position
        (i, j) '''
        if i < 0 or i >= self.board.rows:
            return False

        if j < 0 or j >= self.board.cols:
            return False

        return (i, j) in self.valid_moves


    def move_to(self, i, j):
        ''' Places pawn at i, j. For a valid move, can_move should
        be called first.
        '''
        if self.board.in_range(i, j):
            self.i = i
            self.j = j
            self.cell = self.board[i][j]


    def can_reach_goal(self, board = None):
        ''' True if this player can reach a goal,
        false if it is blocked and there's no way to reach it.
        '''
        if (self.i, self.j) in self.goals: # Already in goal?
            return True

        if board is None:
            board = CellArray(self.board, False)

        if board[self.i][self.j]:
            return False

        board[self.i][self.j] = True

        for i, j in self.valid_moves:
            x = self.i
            y = self.j
            self.move_to(i, j)
            result = self.can_reach_goal(board)
            self.move_to(x, y)
            if result:
                return True

        return False


    @property
    def status(self):
        ''' Returns a string containing 'IJ' coordinates.
        '''
        return str(self.i) + str(self.j) + '%02i' % self.walls



class Wall(Drawable):
    ''' Class for painting a Wall
    '''
    def __init__(self,
        board, # parent object
        surface,
        color,
        row = None, # Wall coordinates
        col = None,
        horiz = None, # whether this wall lays horizontal o vertically
        ):
        self.board = board
        self.screen = surface
        self.horiz = horiz
        self.col = col
        self.row = row
        self.color = color


    def __eq__(self, other):
        return self.horiz == other.horiz and \
                self.col == other.col and \
                self.row == other.row


    def __str__(self):
        return "(%i, %i, %i)" % (self.row, self.col, int(self.horiz))

    @property
    def coords(self):
        ''' Returns a list with 2 t-uples containing coord of
        wall cells. Cells are top / left to the wall.
        '''
        if self.horiz is None or self.col is None or self.row is None:
            return None

        if self.horiz:
            return [(self.row, self.col), (self.row, self.col + 1)]

        return [(self.row, self.col), (self.row + 1, self.col)]


    @property
    def rect(self):
        c = self.coords
        if not c:
            return None

        cell = self.board[self.row][self.col]

        if self.horiz:
            x = cell.x
            y = cell.y + cell.height
            w = self.board.cell_pad + 2 * cell.width
            h = self.board.cell_pad
        else:
            x = cell.x + cell.width
            y = cell.y
            w = self.board.cell_pad
            h = self.board.cell_pad + 2 * cell.width

        return Rect(x, y, w, h)


    def draw(self):
        if self.color is None:
            return

        pygame.draw.rect(screen, self.color, self.rect, 0)


    def collides(self, wall):
        ''' Returns if the given wall collides with this one
        '''
        if self.horiz == wall.horiz:
            wc = wall.coords
            for c in self.coords:
                if c in wc:
                    return True

            return False

        # Only can collide if they form a cross
        if self.col == wall.col and self.row == wall.row:
            return True

        return False


    @property
    def status(self):
        ''' Returns a string containing IJH
        '''
        return str(self.col) + str(self.row) + str(int(self.horiz))


class Cell(Drawable):
    ''' A simple board cell
    '''
    def __init__(self,
        board, # Parent object
        surface, # pygame surface
        i, # row pos. starting from top
        j, # col pos. starting from left
        x = None, # absolute screen position
        y = None, # absolute screen position
        width = CELL_WIDTH,
        height = CELL_HEIGHT,
        color = CELL_COLOR,
        wall_color = WALL_COLOR,
        focus_color = CELL_VALID_COLOR,
        border_color = CELL_BORDER_COLOR,
        border_size = CELL_BORDER_SIZE,
        pawn = None # Reference to the Pawn this cell contains or None
        ):

        Drawable.__init__(self, color, border_color)

        self.surface = surface
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.border_size = border_size
        self.wall_color = wall_color
        self.normal_color = color
        self.focus_color = focus_color
        self.pawn = pawn
        self.board = board
        self.walls = [] # Walls lists
        self.i = i
        self.j = j
        self.has_focus = False # True if mouse on cell
        self.status = '00' # S and E walls

        # Available paths
        self.path = {}
        for d in dirs:
            self.path[d] = True

        if i == 0:
            self.path['N'] = False
        elif j == 0:
            self.path['E'] = False
        elif i == self.board.rows - 1:
            self.path['S'] = False
            self.status == '10'
        elif j == self.board.cols - 1:
            self.path['W'] = False
            self.status == '01'


    def set_path(self, direction, value):
        ''' Sets the path 'N', 'S', 'W', E', to True or False.
        False means no way in that direction. Updates neighbour
        cells accordingly.
        '''
        d = direction.upper()
        self.path[d] = value
        i1, j1 = dirs_delta[d]
        i = self.i + i1
        j = self.j + j1

        s = str(int(value)) # '0' or '1'
        if d == 'S':
            self.status = s + self.status[-1]
        elif d == 'W':
            self.status = self.status[0] + s

        if not self.board.in_range(i, j):
            return # Nothing to do

        self.board[i][j].path[opposite_dirs[d]] = value


    def draw(self):
        Drawable.draw(self)

        if self.pawn:
            self.pawn.draw()


    def onMouseMotion(self, x, y):
        if not self.rect.collidepoint(x, y):
            self.set_focus(False)
            return

        if self.has_focus or self.pawn:
            return

        if self.board.current_player.can_move(self.i, self.j):
            self.set_focus(True)


    def set_focus(self, val):
        val = bool(val)
        if self.has_focus == val:
            return

        self.color = self.focus_color if val else self.normal_color
        self.has_focus = val
        self.draw()


    @property
    def rect(self):
        ''' Returns Cell owns rect
        '''
        return Rect(self.x, self.y, self.width, self.height)



class Board(Drawable):
    ''' Quoridor board.
    This object contains te state of the game.
    '''

    def __init__(self,
        screen,
        rows = DEF_ROWS,
        cols = DEF_COLS,
        cell_padding = CELL_PAD,
        color = BOARD_BG_COLOR,
        border_color = BOARD_BRD_COLOR,
        border_size = BOARD_BRD_SIZE):

        Drawable.__init__(self, color, border_color, border_size)
        self.screen = screen
        self.rows = rows
        self.cols = cols
        self.cell_pad = cell_padding
        self.mouse_wall = None # Wall painted on mouse move
        self.player = 0 # Current player 0 or 1
        self.board = []
        self.computing = False # True if a non-human player is moving

        # Create NETWORK server
        try:
       	    if not is_server_already_running():
                self.server = EnhancedServer(("localhost", PORT))
                REPORT('Servidor activo en localhost:' + str(PORT))
                self.server.register_introspection_functions()
                self.server.register_instance(Functions())
                self.server.start()
        except:
            raise
            self.server = None

        for i in range(rows):
            self.board += [[]]
            for j in range(cols):
                self.board[-1] += [Cell(self, screen, i, j)]

        self.pawns = []
        self.pawns += [Pawn(board = self,
                            color = PAWN_A_COL,
                            border_color = PAWN_BORDER_COL,
                            row = rows - 1,
                            col = cols >> 1 #, # Middle
                            #URL = SERVER_URL + ':%i' % (BASE_PORT + PAWNS)
                            )]
        self.pawns += [Pawn(board = self,
                            color = PAWN_B_COL,
                            border_color = PAWN_BORDER_COL,
                            row = 0,
                            col = cols >> 1 # Middle
                            )]

        self.regenerate_board(CELL_COLOR, CELL_BORDER_COLOR)
        self.num_players = DEFAULT_NUM_PLAYERS
        self.walls = [] # Walls placed on board
        self.draw_players_info()
        self.__AI = []
        self.__AI += [AI(self.pawns[1])]



    def regenerate_board(self, c_color, cb_color, c_width = CELL_WIDTH,
        c_height = CELL_HEIGHT):
        ''' Regenerate board colors and cell positions.
        Must be called on initialization or whenever a screen attribute
        changes (eg. color, board size, etc)
        '''
        Y = self.cell_pad
        for i in range(self.rows):
            X = self.cell_pad

            for j in range(self.cols):
                cell = self.board[i][j]
                cell.x = X
                cell.y = Y
                cell.color = c_color
                cell.border_color = cb_color
                cell.height = c_height
                cell.width = c_width
                cell.pawn = None

                for pawn in self.pawns:
                    if i == pawn.i and j == pawn.j:
                        pawn.cell = cell
                        break

                X += c_width + self.cell_pad

            Y += c_height + self.cell_pad


    def draw(self):
        ''' Draws a squared n x n board, defaults
        to the standard 9 x 9 '''
        Drawable.draw(self)

        for y in range(self.rows):
            for x in range(self.cols):
                self.board[y][x].draw()

        if __DEBUG__:
            for p in self.pawns:
                if p.AI:
                    p.distances.draw()
                    break

        for wall in self.walls:
            wall.draw()


    def cell(self, row, col):
        ''' Returns board cell at the given
        row and column
        '''
        return self.board[row][col]


    def __getitem__(self, i):
        return self.board[i]


    def in_range(self, col, row):
        '''Returns whether te given coordinate are within the board or not
        '''
        return col >= 0 and col < self.cols and row >= 0 and row < self.rows


    def putWall(self, wall):
        ''' Puts the given wall on the board.
        The cells are updated accordingly
        '''
        if wall in self.walls:
            return # If already put, nothing to do

        self.walls += [wall]

        i = wall.row
        j = wall.col

        if wall.horiz:
            self.board[i][j].set_path('S', False)
            self.board[i][j + 1].set_path('S', False)
        else:
            self.board[i][j].set_path('W', False)
            self.board[i + 1][j].set_path('W', False)


    def removeWall(self, wall):
        ''' Removes a wall from the board.
        The cells are updated accordingly
        '''
        if wall not in self.walls:
            return # Already removed, nothing to do

        self.walls.remove(wall)
        i = wall.row
        j = wall.col

        if wall.horiz:
            self.board[i][j].set_path('S', True)
            self.board[i][j + 1].set_path('S', True)
        else:
            self.board[i][j].set_path('W', True)
            self.board[i + 1][j].set_path('W', True)


    def onMouseClick(self, x, y):
        ''' Dispatch mouse click Event
        '''
        cell = self.which_cell(x, y)
        if cell is not None:
            pawn = self.current_player
            if not pawn.can_move(cell.i, cell.j):
                return

            self.do_action((cell.i, cell.j))
            cell.set_focus(False)
            self.draw()

            if self.finished:
                self.draw_player_info(self.player)
                return

            self.next_player()
            self.draw_players_info()
            return

        wall = self.wall(x, y)
        if not wall:
            return

        if self.can_put_wall(wall):
            self.do_action(wall)
            self.next_player()
            self.draw_players_info()


    def onMouseMotion(self, x, y):
        ''' Get mouse motion event and acts accordingly
        '''

        if not self.rect.collidepoint(x, y):
            return

        for row in self.board:
            for cell in row:
                cell.onMouseMotion(x, y)

        if self.which_cell(x, y):
            if self.mouse_wall:
                self.mouse_wall = None
                self.draw()

            return # The focus was on a cell, we're done

        if not self.current_player.walls:
            return # The current player has run out of walls. We're done

        wall = self.wall(x, y)
        if not wall:
            return

        if self.can_put_wall(wall):
            self.mouse_wall = wall
            self.draw()
            wall.draw()


    def can_put_wall(self, wall):
        ''' Returns whether the given wall can be put
        on the board.
        '''
        if not self.current_player.walls:
            return False

        # Check if any wall has already got that place...
        for w in self.walls:
            if wall.collides(w):
                return False

        result = True
        self.putWall(wall)

        for pawn in self.pawns:
            if not pawn.can_reach_goal():
                result = False
                break

        self.removeWall(wall)
        return result


    def wall(self, x, y):
        ''' Returns which wall is below mouse cursor at x, y coords.
        Returns None if no wall matches x, y coords
        '''
        if not self.rect.collidepoint(x, y):
            return None

        # Wall: Guess which top-left cell is it
        j = (x - self.x) / (self.board[0][0].width + self.cell_pad)
        i = (y - self.y) / (self.board[0][0].height + self.cell_pad)
        cell = self.board[i][j]

        # Wall: Guess if it is horizontal or vertical
        horiz = x < (cell.x + cell.width)
        if horiz:
            if j > 7:
                j = 7
        else:
            if i > 7:
                i = 7

        if i > 7 or j > 7:
            return None

        return Wall(self, self.screen, cell.wall_color, i, j, horiz)


    @property
    def x(self):
        ''' Absolute left coordinate
        '''
        return self.board[0][0].x


    @property
    def y(self):
        ''' Absolute left coordinate
        '''
        return self.board[0][0].y


    @property
    def width(self):
        return (self.cell_pad + self.board[0][0].width) * self.cols


    @property
    def height(self):
        return (self.cell_pad + self.board[0][0].height) * self.rows


    @property
    def rect(self):
        return Rect(self.x, self.y, self.width, self.height)


    def next_player(self):
        ''' Switchs to next player
        '''
        self.player = (self.player + 1) % self.num_players
        self.update_pawns_distances()


    def update_pawns_distances(self):
        for pawn in self.pawns:
            pawn.distances.update()


    def which_cell(self, x, y):
        ''' Returns an instance of the cell for which (x, y) screen coord
        matches. Otherwise, returns None if no cell is at (x, y) screen
        coords.
        '''
        for row in self.board:
            for cell in row:
                if cell.rect.collidepoint(x, y):
                    return cell

        return None


    @property
    def current_player(self):
        ''' Returns current player's pawn
        '''
        return self.pawns[self.player]


    def draw_player_info(self, player_num):
        ''' Draws player pawn at board + padding_offset
        '''
        pawn = self.pawns[player_num]
        r = pawn.rect
        r.x = self.rect.x + self.rect.width + PAWN_PADDING
        r.y = (player_num + 1) * (r.height + PAWN_PADDING)
        if self.current_player is pawn:
            pygame.draw.rect(screen, CELL_VALID_COLOR, r, 0)
            pygame.draw.rect(screen, pawn.border_color, r, 2)
        else:
            pygame.draw.rect(screen, self.color, r, 0)

        pawn.draw(r)

        r.x += r.width + 20
        r.width = 6
        pygame.draw.rect(screen, WALL_COLOR, r, 0)

        r.x += r.width * 2 + 10
        r.y += r.height / 2 - 5
        r.height = FONT_SIZE
        r.width *= 3
        pygame.draw.rect(screen, FONT_BG_COLOR, r, 0)  # Erases previous number
        self.msg(r.x, r.y, str(pawn.walls))

        if self.finished and self.current_player == pawn:
            self.msg(r.x + PAWN_PADDING, r.y, "PLAYER %i WINS!" % (1 + self.player))
            x = self.rect.x
            y = self.rect.y + self.rect.height + PAWN_PADDING
            self.msg(x, y, "Press any key to EXIT")


    def msg(self, x, y, str, color = FONT_COLOR, fsize = FONT_SIZE):
        Font = pygame.font.SysFont(None, fsize)
        fnt = Font.render(str, True, color)
        self.screen.blit(fnt, (x, y))


    def draw_players_info(self):
        ''' Calls the above funcion for every player.
        '''
        for i in range(len(self.pawns)):
            self.draw_player_info(i)


    def do_action(self, action):
        ''' Performs a playing action: move a pawn or place a barrier.
        Transmit the action to the network, to inform other players.
        '''
        if isinstance(action, Wall):
            self.putWall(action)
            self.current_player.walls -= 1
            net_act = [action.row, action.col, action.horiz]
        else:
            self.current_player.move_to(*action)
            net_act = list(action)

        for pawn in self.pawns:
            if pawn.NETWORK is not None:
                pawn.NETWORK.do_action(net_act)


    def computer_move(self):
        ''' Performs computer moves for every non-human player
        '''
        try:
            while self.current_player.AI and not self.finished:
                self.draw()
                self.draw_players_info()
                action, x = self.current_player.AI.move()
                print action, x
                self.do_action(action)

                if self.finished:
                    break

                self.next_player()

            self.draw()
            self.draw_players_info()
            self.computing = False

        except AttributeError, v:
            # This exception is only raised (or should be) on users Break
            raise
            pass


    def network_move(self):
        ''' Waits for pawn moving
        '''
        while self.current_player.NETWORK and not self.finished:
            self.draw()
            self.draw_players_info()

            if isinstance(action, Wall):
                self.putWall(action)
                self.current_player.walls -= 1
            else:
                self.current_player.move_to(*action)

            if self.finished:
                break

            self.next_player()

        self.draw()
        self.draw_players_info()
        self.computing = False


    @property
    def finished(self):
        ''' Returns whether the match has finished
        or not.
        '''
        for pawn in self.pawns:
            if (pawn.i, pawn.j) in pawn.goals:
                return True

        return False


    @property
    def status(self):
        ''' Status serialization in a t-uple'''
        result = str(self.player)

        for p in self.pawns:
            result += p.status

        for i in range(self.rows - 1):
            for j in range(self.cols - 1):
                result += self.board[i][j].status

        return result



class CellArray(object):
    ''' Creates an array of the given value, with
    se same size of the board.
    '''
    def __init__(self, board, value):
        self.board = board
        self.rows = board.rows
        self.cols = board.cols

        self.array = [[value for col in range(self.cols)] \
            for row in range(self.rows)]

    def __getitem__(self, i):
        return self.array[i]



class DistArray(CellArray):
    ''' An array which calculates minimun distances
    for each cell.
    '''
    def __init__(self, pawn):
        self.pawn = pawn
        CellArray.__init__(self, pawn.board, 99)

        self.locks = CellArray(self.board, False)
        self.queue = []
        self.MEMOIZE_DISTANCES = {}
        self.MEMO_HITS = 0
        self.MEMO_COUNT = 0
        self.stack = []
        self.update()


    def clean_memo(self):
        ''' Frees memory by removing unused states.
        '''
        L = len(self.board.pawns) * 4 + 1
        k = '.' * L + self.board.status[L:]
        r = re.compile(k.replace('1', '.'))

        for q in self.MEMODISTANCES.keys():
            if not r.match(q):
                del self.MEMODISTANCES[q]


    def update(self):
        ''' Computes minimun distances from the current
        position to the goal.
        '''
        k = self.board.status
        try:
            self.array = copy.deepcopy(self.MEMOIZE_DISTANCES[k])
            self.MEMO_HITS += 1
            return
        except KeyError:
            self.MEMO_COUNT += 1
            pass

        for i in range(self.rows):
            for j in range(self.cols):
                self.array[i][j] = 99

        for i, j in self.pawn.goals:
            self.array[i][j] = 0 # Already in the goal
            self.lock(i, j)

        self.update_distances()
        self.MEMOIZE_DISTANCES[k] = copy.deepcopy(self.array)


    def lock(self, i, j):
        ''' Sets the lock to true, and adds the given coord
        to the queue.
        '''
        if self.locks[i][j]:
            return # Already locked

        self.locks[i][j] = True
        self.queue += [(i, j)]


    def update_cell(self, i, j):
        ''' Updates the cell if not locked yet.
        '''
        if (i, j) in self.pawn.goals:
            return

        values = [self.array[y][x] for y, x in self.pawn.valid_moves_from(i, j)]
        newval = 1 + min(values)

        if newval < self.array[i][j]:
            self.array[i][j] = newval
            self.lock(i, j)


    def update_distances(self):
        cell = self.pawn.cell
        self.pawn.cell = None

        while len(self.queue):
            i, j = self.queue.pop()
            self.locks[i][j] = 0

            for row, col in self.pawn.valid_moves_from(i, j):
                self.update_cell(row, col)

        self.pawn.cell = cell


    def draw(self):
        for i in range(self.rows):
            for j in range(self.cols):
                r = self.board[i][j].rect
                r.x = r.x + r.width - FONT_SIZE
                r.y = r.y + r.height - FONT_SIZE
                r.width = FONT_SIZE
                r.height = FONT_SIZE
                pygame.draw.rect(screen, FONT_BG_COLOR, r, 0)  # Erases previous number
                self.board.msg(r.x, r.y, str(self.array[i][j]))


    def push_state(self):
        self.stack += [self.array]
        CellArray.__init__(self, self.pawn.board, 99)


    def pop_state(self):
        self.array = self.stack.pop()


    @property
    def shortest_path_len(self):
        ''' Return len of the shortest path
        '''
        return min([self.array[i][j] for i, j in self.pawn.valid_moves])



class AI(object):
    ''' This class implements the game AI.
        It could be use to implent an Strategy pattern
    '''
    def __init__(self, pawn, level = 1):
        self.level = level # Level of difficulty
        self.board = pawn.board
        self.__memoize_think = {}

        pawn.AI = self


    @property
    def available_actions(self):
        player = self.pawn
        result = [x for x in player.valid_moves]

        if not player.walls: # Out of walls?
            return result

        try:
            k = self.board.status[1 + 4 * len(self.board.pawns):]
            return result + MEMOIZED_WALLS[k]
        except KeyError:
            pass

        color = self.board[0][0].wall_color
        tmp = []

        for i in range(self.board.rows - 1):
            for j in range(self.board.cols - 1):
                for horiz in (False, True):
                    wall = Wall(self.board, self.board.screen, color, i, j, horiz)
                    if self.board.can_put_wall(wall):
                        tmp += [wall]

        MEMOIZED_WALLS[k] = tmp
        return result + tmp


    def clean_memo(self):
        ''' Removes useless status from the memoized cache.
        '''
        L = 1 + len(self.board.pawns) * 4
        k = self.board.status[L:]
        k = '.' * L + k.replace('1', '.') + '$'
        r = re.compile(k)

        for q in self.__memoize_think.keys():
            if not r.match(q):
                print q
                print k
                del self.__memoize_think[q]


    def move(self):
        ''' Return best move according to the deep level
        '''
        actions = self.pawn.valid_moves
        for move in actions:
            if move in self.pawn.goals:
                return (move, -99)

        move, h, alpha, beta = self.think(bool(self.level % 2))
        self.clean_memo()
        return move, h


    def think(self, MAX, ilevel = 0, alpha = 99, beta = -99):
        ''' Returns best movement with the given level of
        analysis, and returns it as a Wall (if a wall
        must be put) or as a coordinate pair.

        MAX is a boolean with tells if this function is
        looking for a MAX (True) value or a MIN (False) value.
        '''
        global MEMOIZED_NODES, MEMOIZED_NODES_HITS

        k = str(ilevel) + self.board.status[1:]
        try:
            r = self.__memoize_think[k]
            print k
            MEMOIZED_NODES_HITS += 1
            return r
        except KeyError:
            MEMOIZED_NODES += 1
            pass

        result = None
        print alpha, beta
        stop = False

        if ilevel >= self.level: # OK we must return the movement
            HH = 99
            #HH = -99 if MAX else 99

            h0 = self.distances.shortest_path_len
            hh0 = self.board.pawns[(self.board.player + 1) % 2].distances.shortest_path_len
            next_player = (self.board.player + 1) % len(self.board.pawns)

            for action in self.available_actions:
                if isinstance(action, Wall):
                    self.board.putWall(action)
                    self.pawn.walls -= 1
                else:
                    i = self.pawn.i
                    j = self.pawn.j
                    self.pawn.move_to(*action)

                p = self.pawn
                self.board.update_pawns_distances()
                h1 = self.distances.shortest_path_len
                hh1 = min([pawn.distances.shortest_path_len \
                    for pawn in self.board.pawns if pawn is not p])
                h = h1 - hh1 # The heuristic value

                # OK h => my minimum distance - mimimum one of the player nearest
                # to the goal. So the smallest (NEGATIVE) h the better for ME,
                # If we are in a MIN level

                if MAX:
                    h =-h
                    if h > HH:
                        HH = h
                        result = action

                        if HH >= alpha:
                            HH = alpha
                            stop = True
                elif h < HH: # MIN
                        HH = h
                        result = action

                        if HH <= beta:
                            HH = beta
                            stop = True

                elif self.level == 0 and h == HH and h1 <= h0 and hh1 > hh0:
                    result = action

                #  Undo action
                if isinstance(action, Wall):
                    self.board.removeWall(action)
                    self.pawn.walls += 1
                else:
                    self.pawn.move_to(i, j)

                if stop:
                    break

            self.__memoize_think[k] = (result, HH, alpha, beta)
            return (result, HH, alpha, beta)

        # Not a leaf in the search tree. Alpha-Beta minimax
        HH = -99 if MAX else 99
        player = self.board.current_player
        player.distances.push_state()
        r = self.available_actions

        for action in r: #self.available_actions:
            if isinstance(action, Wall):
                self.board.putWall(action)
                self.pawn.walls -= 1
            else:
                print action, ilevel
                i = self.pawn.i
                j = self.pawn.j
                self.pawn.move_to(*action)

            self.board.next_player()
            dummy, h, alpha1, beta1 = self.think(not MAX, ilevel + 1, alpha, beta)
            print action, '|', dummy, h, '<<<'
            self.previous_player()

            if MAX:
                print h, HH
                if h > HH: # MAX
                    result, HH = action, h
                    if HH >= alpha:
                        HH = alpha
                        stop = True
                    else:
                        beta = HH
            else:
                if h < HH: # MIN
                    result, HH = action, h
                    if HH <= beta:
                        HH = beta
                        stop = True
                    else:
                        alpha = HH

            #  Undo action
            if isinstance(action, Wall):
                self.board.removeWall(action)
                self.pawn.walls += 1
            else:
                self.pawn.move_to(i, j)

            if stop:
                break

        player.distances.pop_state()
        self.__memoize_think[k] = (result, HH, alpha, beta)
        print result
        return (result, HH, alpha, beta)


    @property
    def pawn(self):
        return self.board.current_player


    @property
    def distances(self):
        return self.pawn.distances


    def previous_player(self):
        ''' Switchs to previous player.
        '''
        self.board.player = (self.board.player + self.board.num_players - 1) %\
            self.board.num_players



class Functions:
    ''' Class with XML exported functions.
    '''
    def __init__(self):
        ''' ...
        '''
        print "hi"

    def alive(self):
        ''' Returns True if the server is alive.
        '''
        return True


    def do_action(self, T):
        if len(T) == 3: # It's a wall
            pass
        else:
            t = tuple(T)

        if board.current_player.NETWORK:
            board.do_action(T)
            return True

        return False # Not allowed




def dispatch(events):
    for event in events:
        if event.type == QUIT:
            return False

        if hasattr(event, 'key'):
            if event.key == K_ESCAPE or board.finished:
                return False

        if board.finished or board.computing or board.current_player.NETWORK:
            continue

        if event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            board.onMouseClick(x, y)

        if event.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            board.onMouseMotion(x, y)

    return True




if __name__ == '__main__':
    try:
        pygame.init()
        clock = pygame.time.Clock()
        window = pygame.display.set_mode((800, 600))
        pygame.display.set_caption(GAME_TITLE)
        screen = pygame.display.get_surface()

        screen.fill(Color(255,255,255))
        board = Board(screen)
        board.draw()

        cont = True
        while cont:
            clock.tick(FRAMERATE)
            pygame.display.flip()

            if not board.computing and not board.finished:
                if board.current_player.AI:
                    board.computing = True
                    thread = threading.Thread(target = board.computer_move)
                    thread.start()
                else:
                    try:
                        if board.current_player.NETWORK:
                            board.network_move()
                    except:
                        REPORT('Network error...')
                        pass

            cont = dispatch(pygame.event.get())

        del board.rows #
        pygame.quit()
    except AttributeError:
        raise

    print 'Memoized nodes:', MEMOIZED_NODES
    print 'Memoized nodes hits:', MEMOIZED_NODES_HITS

    for pawn in board.pawns:
        print 'Memoized distances for [%i]: %i' % (pawn.id, pawn.distances.MEMO_COUNT)
        print 'Memoized distances hits for [%i]: %i' % (pawn.id, pawn.distances.MEMO_HITS)
