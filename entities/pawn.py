# -*- coding: utf-8 -*-

import time
import pygame
import socket
import xmlrpc
from typing import List, Set

import config as cfg
import core
from helpers import log

from .drawable import Drawable
from .cell import Cell
from .coord import Coord


class Pawn(Drawable):
    """ Class defining a player pawn
    """
    goals: Set[Coord] = None

    def __init__(self,
                 screen: pygame.Surface,
                 board,
                 color,
                 border_color=cfg.PAWN_BORDER_COL,
                 coord=None,
                 walls=cfg.NUM_WALLS,
                 width=cfg.CELL_WIDTH - cfg.CELL_PAD,
                 height=cfg.CELL_HEIGHT - cfg.CELL_PAD,  # Set to True so the computer moves this pawn
                 url=None  # Set
                 ):
        super().__init__(screen, color, border_color)
        self.width = width
        self.height = height
        self._coord = coord
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
    def cell(self) -> Cell:
        if self.coord is None:
            return None

        return self.board.get_cell(self.coord)

    @cell.setter
    def cell(self, cell):
        if self.__cell is not None:  # Remove old get_cell if any
            self.__cell.pawn = None

        self.__cell = cell
        if cell is not None:
            self.__cell.pawn = self

    def set_goal(self):
        """ Sets a list of possible goals (cells) for this
        player.
        """
        if self.coord.row == 0:
            self.goals = {Coord(self.board.rows - 1, x) for x in range(self.board.cols)}
        elif self.coord.row == self.board.rows - 1:
            self.goals = {Coord(0, x) for x in range(self.board.cols)}
        elif self.coord.col == self.board.cols - 1:
            self.goals = {Coord(x, 0) for x in range(self.board.cols)}
        else:
            self.goals = {Coord(x, self.board.cols - 1) for x in range(self.board.rows)}

    def draw(self, r=None):
        if self.coord is None:
            return

        if r is None:
            r = self.rect

        pygame.draw.ellipse(self.board.screen, self.color, r, 0)
        pygame.draw.ellipse(self.board.screen, self.border_color, r, 2)

    @property
    def rect(self):
        return self.board.get_cell(self.coord).rect

    def can_go(self, direction: int) -> List[Coord]:
        """ Direction is one of 'N', 'S', 'E', 'W'
        Returns te list of new coordinates the pawn can move by going into that direction, or None otherwise.
        Usually it's just one coordinate or empty (not possible), but sometimes it can be two coordinates if the
        pawn can move diaginally by jumping a confronting opponent.
        """
        assert self.cell is not None, "Cell({}, {}) is uninitialized".format(self.coord.row, self.coord.col)

        if self.cell.path[direction] is False:
            return []  # Blocked in that direction

        new_coord = self.coord + cfg.DIRS_DELTA[direction]
        if not self.board.in_range(new_coord):
            return []

        if self.board.get_cell(new_coord).pawn is None:  # Is it free?
            return [new_coord]

        # Ok there's a pawn at I, J. Check for adjacent
        result = []

        for di in cfg.DIRS:  # Check for any direction
            if di == cfg.OPPOSITE_DIRS[direction]:
                continue

            if self.board.get_cell(new_coord).path[di]:
                new_coord2 = new_coord + cfg.DIRS_DELTA[di]
                if not self.board.in_range(new_coord2):
                    continue

                if self.board.get_cell(new_coord2).pawn is None:
                    result.append(new_coord2)

        return result

    @property
    def valid_moves(self) -> List[Coord]:
        """ Returns a list of valid moves as list of coordinates
        """
        result: List[Coord] = []

        if self.cell is None:
            return result

        for d in cfg.DIRS:  # Try each direction
            result.extend(self.can_go(d))

        return result

    def valid_moves_from(self, coord: Coord) -> List[Coord]:
        """ Returns a list of valid moves from coord(row, col).
        (i, j) can be a different position from the
        current one.
        """
        current_pos = self.coord  # Saves current position
        self._coord = coord
        result = self.valid_moves
        self._coord = current_pos  # Restores current position

        return result

    def can_move(self, coord: Coord) -> bool:
        """ Returns whether the pawn can move to position
        (i, j)
        """
        return coord in self.valid_moves

    def move_to(self, coord: Coord) -> None:
        """ Places pawn at i, j. For a valid move, can_move should
        be called first.
        """
        if self.board.in_range(coord):
            self._coord = coord
            self.cell = self.board.get_cell(self.coord)

    def can_reach_goal(self, board=None) -> bool:
        """ True if this player can reach a goal,
        false if it is blocked and there's no way to reach it.
        """
        if self.coord in self.goals:  # Already in goal?
            return True

        if board is None:
            board = core.CellArray(self.board, False)

        if board.get_cell(self.coord):
            return False

        board.set_cell(self.coord, True)
        for move in self.valid_moves:
            current_pos = self.coord
            self.move_to(move)
            result = self.can_reach_goal(board)
            self.move_to(current_pos)
            if result:
                return True

        return False

    @property
    def state(self):
        """ Returns a string containing i,j,w being i, j the pawn coordinates
        and w the number of remaining walls
        """
        return '%i%i%02i' % (self._coord.row, self._coord.col, self.walls)

    @property
    def coord(self) -> Coord:
        """ Returns pawn coordinate (row, col)
        """
        return self._coord

    @coord.setter
    def coord(self, coord: Coord) -> None:
        self.move_to(coord)
