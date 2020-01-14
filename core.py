# -*- coding: utf-8 -*-

import re
import typing
import pygame

import config as cfg

# Core (shared) data. Must be initialized invoking init()
# This global counter counts the total number of players instantiated (Pawns)
PAWNS = None

# Memoized put-wall cache
MEMOIZED_WALLS = None

# --- Statistics ---
MEMOIZED_NODES = None  # Memoized AI Nodes
MEMOIZED_NODES_HITS = None  # Memoized Cache hits

# --- Game Board (Singleton)
BOARD = None


class CellArray:
    """ Creates an array of the given value, with
    the same size as the board.
    """
    def __init__(self, board, value: any):
        self.board = board
        self.rows = board.rows
        self.cols = board.cols
        self.array = [[value for _ in range(self.cols)] for _ in range(self.rows)]

    def __getitem__(self, i) -> typing.List[any]:
        return self.array[i]


class DistArray(CellArray):
    """ An array which calculates minimum distances
    for each cell.
    """
    def __init__(self, pawn):
        self.pawn = pawn
        CellArray.__init__(self, pawn.board, cfg.INF)

        self.locks = CellArray(self.board, False)
        self.queue = []
        self.MEMOIZE_DISTANCES = {}
        self.MEMO_HITS = 0
        self.MEMO_COUNT = 0
        self.stack = []
        self.update()

    def clean_memo(self):
        """ Frees memory by removing unused states.
        """
        l_ = 1 + len(self.board.pawns) * 4
        k = self.board.status[l_:]
        k = '.' * l_ + k.replace('1', '.') + '$'
        r = re.compile(k)

        for q in list(self.MEMOIZE_DISTANCES.keys()):
            if not r.match(q):
                del self.MEMOIZE_DISTANCES[q]

    def update(self):
        """ Computes minimum distances from the current
        position to the goal.
        """
        k = self.board.status
        try:
            self.array = self.MEMOIZE_DISTANCES[k]
            self.MEMO_HITS += 1
            return
        except KeyError:
            self.MEMO_COUNT += 1

        for i in range(self.rows):
            for j in range(self.cols):
                self.array[i][j] = cfg.INF

        for i, j in self.pawn.goals:
            self.array[i][j] = 0  # Already in the goal
            self.lock(i, j)

        self.update_distances()
        self.MEMOIZE_DISTANCES[k] = self.array

    def lock(self, i, j):
        """ Sets the lock to true, and adds the given coord
        to the queue.
        """
        if self.locks[i][j]:
            return  # Already locked

        self.locks[i][j] = True
        self.queue += [(i, j)]

    def update_cell(self, i, j):
        """ Updates the cell if not locked yet.
        """
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
        """ Displays distance numbers in the screen
        """
        if not cfg.__DEBUG__:
            return

        for i in range(self.rows):
            for j in range(self.cols):
                r = self.board[i][j].rect
                r.x = r.x + r.width - cfg.FONT_SIZE
                r.y = r.y + r.height - cfg.FONT_SIZE
                r.width = cfg.FONT_SIZE
                r.height = cfg.FONT_SIZE
                pygame.draw.rect(self.pawn.screen, cfg.FONT_BG_COLOR, r, 0)  # Erases previous number
                self.board.msg(r.x, r.y, str(self.array[i][j]))

    def push_state(self):
        self.stack.append(self.array)
        CellArray.__init__(self, self.pawn.board, cfg.INF)

    def pop_state(self):
        self.array = self.stack.pop()

    @property
    def shortest_path_len(self):
        """ Return len of the shortest path
        """
        return min([self.array[i][j] for i, j in self.pawn.valid_moves])


def init():
    global PAWNS
    global MEMOIZED_WALLS
    global MEMOIZED_NODES
    global MEMOIZED_NODES_HITS
    global BOARD

    PAWNS = 0
    MEMOIZED_WALLS = {}
    MEMOIZED_NODES = 0
    MEMOIZED_NODES_HITS = 0
    BOARD = None
