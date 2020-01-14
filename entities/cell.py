# -*- coding: utf-8 -*-

from typing import List
import pygame

import config as cfg
from .drawable import Drawable
from .coord import Coord


class Cell(Drawable):
    """ A simple board get_cell
    """
    def __init__(self,
                 screen: pygame.Surface,  # Screen display object (pygame surface)
                 board,  # Parent object
                 coord: Coord,
                 x=None,  # absolute screen position
                 y=None,  # absolute screen position
                 width=cfg.CELL_WIDTH,
                 height=cfg.CELL_HEIGHT,
                 color=cfg.CELL_COLOR,
                 wall_color=cfg.WALL_COLOR,
                 focus_color=cfg.CELL_VALID_COLOR,
                 border_color=cfg.CELL_BORDER_COLOR,
                 border_size=cfg.CELL_BORDER_SIZE,
                 pawn=None  # Reference to the Pawn this get_cell contains or None
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
        self.coord = coord
        self.has_focus: bool = False  # True if mouse on get_cell

        # Available paths
        self.path: List[bool] = [True] * len(cfg.DIRS)

        if coord.row == 0:
            self.set_path(cfg.DIR.N, False)
        elif coord.row == self.board.rows - 1:
            self.set_path(cfg.DIR.S, False)

        if coord.col == 0:
            self.set_path(cfg.DIR.E, False)
        elif coord.col == self.board.cols - 1:
            self.set_path(cfg.DIR.W, False)

    def set_path(self, direction: int, value: bool) -> None:
        """ Sets the path 'N', 'S', 'W', E', to True or False.
        False means no way in that direction. Updates neighbour
        cells accordingly.
        """
        self.path[direction] = value
        new_coord = self.coord + cfg.DIRS_DELTA[direction]
        if not self.board.in_range(new_coord):
            return  # Nothing to do

        self.board.get_cell(new_coord).path[cfg.OPPOSITE_DIRS[direction]] = value

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

        if self.board.current_player.can_move(self.coord):
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

    @property
    def state(self) -> str:
        """ Returns Cell state as a string
        """
        return ''.join('01'[self.path[d]] for d in (cfg.DIR.S, cfg.DIR.W))
