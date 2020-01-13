# -*- coding: utf-8 -*-

import pygame

import config as cfg
from .drawable import Drawable


class Cell(Drawable):
    """ A simple board cell
    """
    def __init__(self,
                 screen: pygame.Surface,  # Screen display object (pygame surface)
                 board,  # Parent object
                 i,  # row pos. starting from top
                 j,  # col pos. starting from left
                 x=None,  # absolute screen position
                 y=None,  # absolute screen position
                 width=cfg.CELL_WIDTH,
                 height=cfg.CELL_HEIGHT,
                 color=cfg.CELL_COLOR,
                 wall_color=cfg.WALL_COLOR,
                 focus_color=cfg.CELL_VALID_COLOR,
                 border_color=cfg.CELL_BORDER_COLOR,
                 border_size=cfg.CELL_BORDER_SIZE,
                 pawn=None  # Reference to the Pawn this cell contains or None
                 ):

        super().__init__(screen, color, border_color, border_size)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.wall_color = wall_color
        self.normal_color = color
        self.focus_color = focus_color
        self.pawn = pawn
        self.board = board
        self.walls = []  # Walls lists
        self.i = i
        self.j = j
        self.has_focus = False  # True if mouse on cell
        self.status = '00'  # S and E walls

        # Available paths
        self.path = {}
        for d in cfg.dirs:
            self.path[d] = True

        if i == 0:
            self.path['N'] = False
        elif j == 0:
            self.path['E'] = False
        elif i == self.board.rows - 1:
            self.path['S'] = False
            self.status = '10'
        elif j == self.board.cols - 1:
            self.path['W'] = False
            self.status = '01'

    def set_path(self, direction, value):
        """ Sets the path 'N', 'S', 'W', E', to True or False.
        False means no way in that direction. Updates neighbour
        cells accordingly.
        """
        d = direction.upper()
        self.path[d] = value
        i1, j1 = cfg.dirs_delta[d]
        i = self.i + i1
        j = self.j + j1

        s = str(int(value))  # '0' or '1'
        if d == 'S':
            self.status = s + self.status[-1]
        elif d == 'W':
            self.status = self.status[0] + s

        if not self.board.in_range(i, j):
            return  # Nothing to do

        self.board[i][j].path[cfg.opposite_dirs[d]] = value

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
        """ Returns Cell owns rect
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
