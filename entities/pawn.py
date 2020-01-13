# -*- coding: utf-8 -*-

import time
import pygame
import socket
import xmlrpc
import typing

import config as cfg
import core
from helpers import log

from .drawable import Drawable


class Coord(typing.NamedTuple):
    row: int
    col: int


class Pawn(Drawable):
    """ Class defining a player pawn
    """
    goals = None

    def __init__(self,
                 screen: pygame.Surface,
                 board,
                 color,
                 border_color=cfg.PAWN_BORDER_COL,
                 row=None,
                 col=None,
                 walls=cfg.NUM_WALLS,
                 width=cfg.CELL_WIDTH - cfg.CELL_PAD,
                 height=cfg.CELL_HEIGHT - cfg.CELL_PAD,  # Set to True so the computer moves this pawn
                 url=None  # Set
                 ):
        super().__init__(screen, color, border_color)
        self.width = width
        self.height = height
        self.i = row
        self.j = col
        self.board = board
        self.walls = walls  # Walls per player
        self.__cell = None
        self.set_goal()
        self.id = core.PAWNS
        self.distances = core.DistArray(self)
        self.AI = None
        self.is_network_player = False
        self.percent = None

        if url is not None:
            log('Connecting to server [%s]' % url)
            network = None
            count = 0
            maxtries = 10
            while count < maxtries:
                count += 1
                try:
                    network = xmlrpc.client.Server(url, allow_none=True, encoding='utf-8')
                    log('Pinging server...')
                    if network.alive():
                        log('Done!')
                        break
                except socket.error:
                    log('Waiting for server...')
                    time.sleep(1.5)

            log('Connected!')
            self.NETWORK = network
            self.is_network_player = True
        else:
            self.NETWORK = None

        core.PAWNS += 1

    @property
    def cell(self):
        row, col = (self.i, self.j)
        if row is None and col is None:
            return None

        return self.board[row][col]

    @cell.setter
    def cell(self, cell):
        if self.__cell is not None:  # Remove old cell if any
            self.__cell.pawn = None

        self.__cell = cell
        if cell is not None:
            self.__cell.pawn = self

    def set_goal(self):
        """ Sets a list of possible goals (cells) for this
        player.
        """
        if self.i == 0:
            self.goals = [(self.board.rows - 1, x) for x in range(self.board.cols)]
        elif self.i == self.board.rows - 1:
            self.goals = [(0, x) for x in range(self.board.cols)]
        elif self.j == self.board.cols - 1:
            self.goals = [(x, 0) for x in range(self.board.cols)]
        else:
            self.goals = [(x, self.board.cols - 1) for x in range(self.board.rows)]

    def draw(self, r=None):
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
        """ One of 'N', 'S', 'E', 'W'
        Returns False if can't go in that direction. Otherwise, returns
        a list of possible coordinates.
        """
        if self.cell is None:
            return False  # Uninitialized

        d = direction.upper()
        if d not in cfg.dirs:
            return False  # Unknown move

        if self.cell.path[d] is False:
            return False  # Blocked in that direction

        i, j = cfg.dirs_delta[d]
        i += self.i
        j += self.j

        if not self.board.in_range(i, j):
            return False

        if self.board[i][j].pawn is None:  # Is it free?
            return [(i, j)]

        # Ok there's a pawn at I, J. Check for adjacent
        result = []

        for di in cfg.dirs:  # Check for any direction
            if di == cfg.opposite_dirs[d]:
                continue

            if self.board[i][j].path[di]:
                i2, j2 = cfg.dirs_delta[di]
                i2 += i
                j2 += j

                if not self.board.in_range(i2, j2):
                    continue

                if self.board[i2][j2].pawn is None:
                    result += [(i2, j2)]

        return result

    @property
    def valid_moves(self):
        """ Returns a list of valid moves as a tuples of (row, col)
        coordinates
        """
        result = []

        if self.cell is None:
            return result

        for d in cfg.dirs:  # Try each direction
            coords = self.can_go(d)
            if coords:
                result += coords

        return result

    def valid_moves_from(self, i, j):
        """ Returns a list of valid moves from (i, j).
        (i, j) can be a different position from the
        current one.
        """
        current_pos = self.i, self.j  # Saves current position
        self.i, self.j = i, j
        result = self.valid_moves
        self.i, self.j = current_pos  # Restores current position

        return result

    def can_move(self, i, j):
        """ Returns whether the pawn can move to position
        (i, j)
        """
        if i < 0 or i >= self.board.rows:
            return False

        if j < 0 or j >= self.board.cols:
            return False

        return (i, j) in self.valid_moves

    def move_to(self, row: int, col: int) -> None:
        """ Places pawn at i, j. For a valid move, can_move should
        be called first.
        """
        if self.board.in_range(row, col):
            self.i, self.j = row, col
            self.cell = self.board[row][col]

    def can_reach_goal(self, board=None):
        """ True if this player can reach a goal,
        false if it is blocked and there's no way to reach it.
        """
        if (self.i, self.j) in self.goals:  # Already in goal?
            return True

        if board is None:
            board = core.CellArray(self.board, False)

        if board[self.i][self.j]:
            return False

        board[self.i][self.j] = True

        for i, j in self.valid_moves:
            i_, j_ = self.i, self.j
            self.move_to(i, j)
            result = self.can_reach_goal(board)
            self.move_to(i_, j_)
            if result:
                return True

        return False

    @property
    def status(self):
        """ Returns a string containing 'IJ' coordinates.
        """
        return str(self.i) + str(self.j) + '%02i' % self.walls

    @property
    def coord(self) -> Coord:
        """ Returns pawn coordinate (row, col)
        """
        return Coord(self.i, self.j)

    @coord.setter
    def coord(self, coord: Coord) -> None:
        self.move_to(coord.row, coord.col)
