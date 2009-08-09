#!/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pygame
from pygame.locals import *
from pygame import Color
from pygame import Rect

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

# Cell colors
CELL_BORDER_COLOR = Color(40, 40, 40)
CELL_COLOR = Color(120, 90, 60)
CELL_VALID_MOVE = Color(40, 120, 120) # Cyan

# Wall Color
WALL_COLOR = Color(10, 10, 10)

# Pawns color
PAWN_A_COL = Color(158, 60, 60) # Red
PAWN_B_COL = Color(60, 60, 158) # Blue
PAWN_BORDER_COL = Color(188, 188, 80) # Yellow

# Avaiable directions
dirs = ['N', 'S', 'E', 'W']
dirs_delta = {'N': (-1, 0), 'S': (+1, 0), 'E': (0, -1), 'W': (0, +1)}


def manhattan((a, b), (c, d)):
    ''' Manhattan distance
    '''
    return abs(a - c) + abs(b - d)


class Drawable(object):
    ''' Abstract drawable class
    '''
    def __init__(self, color = None,
                    border_color = None):
        self.color = color
        self.border_color = border_color

    def draw(self):
        if self.color is None or self.border_color is None:
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
            height = CELL_HEIGHT - CELL_PAD):
        self.color = color
        self.border_color = border_color
        self.width = width
        self.height = height
        self.i = row
        self.j = col
        self.board = board
        self.walls = walls # Walls per player
        self.__cell = None


    def __set_cell(self, cell):
        if self.__cell is not None: # Remove old cell if any
            self.__cell.pawn = None

        self.__cell = cell
        self.__cell.pawn = self


    def __get_cell(self):
        row, col = (self.i, self.j)
        if row is None and col is None:
            return None

        return self.board[row][col]

    cell = property(__get_cell, __set_cell)


    def draw(self):
        if self.i is None or self.j is None:
            return

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
        if self.board[I][J].pawn is None: # Is it free?
            return [(I, J)]

        # Ok there's a pawn at I, J. Check for adjacent
        result = []
        back = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}

        for di in dirs: # Check for any direction
            if di == back[d]:
                continue

            if self.board[I][J].path[di]:
                Ia, Ja = dirs_delta[di]
                Ia += I
                Ja += J
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



class Wall(Drawable):
    ''' Class for painting a Wall
    '''
    def __init__(self,
        board, # parent object
        surface,
        row = None, # Wall coordinates
        col = None,
        horiz = None, # whether this wall lays horizontal o vertically
        ):
        self.board = board
        self.surface = surface
        self.horiz = horiz
        self.col = col
        self.row = row

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
        self.pawn = pawn
        self.board = board
        self.walls = [] # Walls lists
        self.i = i
        self.j = j

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
        elif j == self.board.cols - 1:
            self.path['W'] = False


    def draw(self):
        Drawable.draw(self)

        if self.pawn:
            self.pawn.draw()


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
        cell_padding = CELL_PAD):

        self.screen = screen
        self.rows = rows
        self.cols = cols
        self.cell_pad = cell_padding

        self.board = []
        for i in range(rows):
            self.board += [[]]
            for j in range(cols):
                self.board[-1] += [Cell(self, screen, i, j)]

        self.pawns = []
        self.pawns += [Pawn(board = self,
                            color = PAWN_A_COL,
                            border_color = PAWN_BORDER_COL,
                            row = 0,
                            col = cols >> 1 # Middle top
                            )]

        self.pawns += [Pawn(board = self,
                            color = PAWN_B_COL,
                            border_color = PAWN_BORDER_COL,
                            row = rows - 1,
                            col = cols >> 1 # Middle top
                            )]
        self.regenerate_board(CELL_COLOR, CELL_BORDER_COLOR)
        self.player = 0 # Current player 0 or 1
        self.num_players = DEFAULT_NUM_PLAYERS



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
        for y in range(self.rows):
            for x in range(self.cols):
                self.board[y][x].draw()


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


    def onMouseClick(self):
        ''' Dispatch mouse click Event
        '''
        x, y = pygame.mouse.get_pos()

        for row in self.board:
            for cell in row:
                if cell.rect.collidepoint(x, y): # Click on cell?
                    pawn = self.pawns[self.player]
                    if not pawn.can_move(cell.i, cell.j):
                        return

                    pawn.move_to(cell.i, cell.j)
                    pawn.cell = cell
                    self.draw()
                    self.next_player()
                    return

    @property
    def rect(self):
        w = (self.cell_pad + self.board[0][0].width) * self.cols
        h = (self.cell_pad + self.board[0][0].height) * self.rows
        return Rect(self.board[0][0].x, self.board[0][0].y, width, height)


    def onMouseMotion(self):
        ''' Get mouse motion event and acts accordingly
        '''
        x, y = pygame.mouse.get_pos()


    def next_player(self):
        ''' Switchs to next player
        '''
        self.player = (self.player + 1) % self.num_players



def input(events):
    for event in events:
        if event.type == QUIT:
            sys.exit(0)

        if hasattr(event, 'key'):
            if event.key == K_ESCAPE:
                sys.exit(0)

        if event.type == MOUSEBUTTONDOWN:
            board.onMouseClick()

        if event.type == MOUSEMOTION:
            board.onMouseMotion()


pygame.init()
window = pygame.display.set_mode((800, 600))
pygame.display.set_caption(GAME_TITLE)
screen = pygame.display.get_surface()

screen.fill(Color(255,255,255))
board = Board(screen)
board.draw()

while True:
    pygame.display.flip()
    input(pygame.event.get())

