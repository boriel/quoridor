# -*- coding: utf-8 -*-

import time
import pygame
import socket
import xmlrpc
from typing import List, Tuple, NamedTuple

import config as cfg
import core
from helpers import log

from .drawable import Drawable


class Coord(NamedTuple):
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

    def can_go(self, direction: int) -> List[Tuple[int, int]]:
        """ Direction is one of 'N', 'S', 'E', 'W'
        Returns te list of new coordinates the pawn can move by going into that direction, or None otherwise.
        Usually it's just one coordinate or empty (not possible), but sometimes it can be two coordinates if the
        pawn can move diaginally by jumping a confronting opponent.
        """
        assert self.cell is not None, "Cell({}, {}) is uninitialized".format(self.i, self.j)

        if self.cell.path[direction] is False:
            return []  # Blocked in that direction

        i, j = cfg.DIRS_DELTA[direction]
        i += self.i
        j += self.j

        if not self.board.in_range(i, j):
            return []

        if self.board[i][j].pawn is None:  # Is it free?
            return [(i, j)]

        # Ok there's a pawn at I, J. Check for adjacent
        result = []

        for di in cfg.DIRS:  # Check for any direction
            if di == cfg.OPPOSITE_DIRS[direction]:
                continue

            if self.board[i][j].path[di]:
                i2, j2 = cfg.DIRS_DELTA[di]
                i2 += i
                j2 += j

                if not self.board.in_range(i2, j2):
                    continue

                if self.board[i2][j2].pawn is None:
                    result.append((i2, j2))

        return result

    @property
    def valid_moves(self) -> List[Tuple[int, int]]:
        """ Returns a list of valid moves as a tuples of (row, col)
        coordinates
        """
        result: List[Tuple[int, int]] = []

        if self.cell is None:
            return result

        for d in cfg.DIRS:  # Try each direction
            result.extend(self.can_go(d))

        return result

    def valid_moves_from(self, i: int, j: int) -> List[Tuple[int, int]]:
        """ Returns a list of valid moves from (i, j).
        (i, j) can be a different position from the
        current one.
        """
        current_pos = self.i, self.j  # Saves current position
        self.i, self.j = i, j
        result = self.valid_moves
        self.i, self.j = current_pos  # Restores current position

        return result

    def can_move(self, i: int, j: int) -> bool:
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

    def can_reach_goal(self, board=None) -> bool:
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
    def state(self):
        """ Returns a string containing i,j,w being i, j the pawn coordinates
        and w the number of remaining walls
        """
        return '%i%i%02i' % (self.i, self.j, self.walls)

    @property
    def coord(self) -> Coord:
        """ Returns pawn coordinate (row, col)
        """
        return Coord(self.i, self.j)

    @coord.setter
    def coord(self, coord: Coord) -> None:
        self.move_to(coord.row, coord.col)
