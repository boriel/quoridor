# -*- coding: utf-8 -*-

import pygame

from .drawable import Drawable


class Wall(Drawable):
    """ Class for painting a Wall
    """
    def __init__(self,
                 screen: pygame.Surface,
                 board,  # parent object
                 color: pygame.Color,
                 row: int = None,  # Wall coordinates
                 col: int = None,
                 horiz: bool = None,  # whether this wall lays horizontal o vertically
                 ):
        super().__init__(screen, color)
        self.board = board
        self.horiz: bool = horiz
        self.col: int = col
        self.row: int = row

    def __eq__(self, other) -> bool:
        return self.horiz == other.horiz and \
               self.col == other.col and \
               self.row == other.row

    def __repr__(self):
        return "<Wall: %i, %i, %i>" % (self.row, self.col, int(self.horiz))

    def __hash__(self):
        return hash((self.horiz, self.row, self.col))

    @property
    def coords(self):
        """ Returns a list with 2 t-uples containing coord of
        wall cells. Cells are top / left to the wall.
        """
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

        return pygame.Rect(x, y, w, h)

    def draw(self):
        if self.color is None:
            return

        pygame.draw.rect(self.screen, self.color, self.rect, 0)

    def collides(self, wall):
        """ Returns if the given wall collides with this one
        """
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
        """ Returns a string containing IJH
        """
        return str(self.col) + str(self.row) + str(int(self.horiz))
