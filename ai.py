# -*- coding: utf-8 -*-

import re

from helpers import log, LogLevel
import core
import config as cfg
from config import INF

from entities.wall import Wall


class AI(object):
    """ This class implements the game AI.
    It could be use to implement an Strategy pattern
    """
    def __init__(self, pawn, level=1):
        self.level = level  # Level of difficulty
        self.board = pawn.board
        self.__memoize_think = {}

        pawn.AI = self
        log('Player %i is moved by computers A.I. with level %i' % (pawn.id, level), LogLevel.INFO)

    @property
    def available_actions(self):
        player = self.pawn
        result = [x for x in player.valid_moves]

        if not player.walls:  # Out of walls?
            return result

        k = self.board.status[1 + 4 * len(self.board.pawns):]
        try:
            return result + core.MEMOIZED_WALLS[k]
        except KeyError:
            pass

        color = self.board[0][0].wall_color
        tmp = []

        for i in range(self.board.rows - 1):
            for j in range(self.board.cols - 1):
                for horiz in (False, True):
                    wall = Wall(self.board.screen, self.board, color, i, j, horiz)
                    if self.board.can_put_wall(wall):
                        tmp.append(wall)

        core.MEMOIZED_WALLS[k] = tmp
        return result + tmp

    def clean_memo(self):
        """ Removes useless status from the memoized cache.
        """
        L = 1 + len(self.board.pawns) * 4
        k = self.board.status[L:]
        k = '.' * L + k.replace('1', '.') + '$'
        r = re.compile(k)

        for q in list(self.__memoize_think.keys()):
            if not r.match(q):
                del self.__memoize_think[q]

    def move(self):
        """ Return best move according to the deep level
        """
        actions = self.pawn.valid_moves
        for move in actions:
            if move in self.pawn.goals:
                return move, -INF

        self.pawn.percent = 0  # Percentage done
        move, h, alpha, beta = self.think(bool(self.level % 2))
        self.clean_memo()
        self.distances.clean_memo()
        return move, h

    def think(self, MAX, ilevel=0, alpha=INF, beta=-INF):
        """ Returns best movement with the given level of
        analysis, and returns it as a Wall (if a wall
        must be put) or as a coordinate pair.

        MAX is a boolean with tells if this function is
        looking for a MAX (True) value or a MIN (False) value.
        """
        k = str(ilevel) + self.board.status[1:]
        try:
            r = self.__memoize_think[k]
            core.MEMOIZED_NODES_HITS += 1
            return r
        except KeyError:
            core.MEMOIZED_NODES += 1
            pass

        result = None
        # __DEBUG__
        # print(alpha, beta)
        stop = False

        if ilevel >= self.level:  # OK we must return the movement
            HH = INF
            h0 = self.distances.shortest_path_len
            hh0 = self.board.pawns[(self.board.player + 1) % 2].distances.shortest_path_len
            # next_player = (self.board.player + 1) % len(self.board.pawns)

            for action in self.available_actions:
                if isinstance(action, Wall):
                    self.board.putWall(action)
                    self.pawn.walls -= 1
                else:
                    i, j = self.pawn.i, self.pawn.j
                    self.pawn.move_to(*action)

                p = self.pawn
                self.board.update_pawns_distances()
                h1 = self.distances.shortest_path_len
                hh1 = min([pawn.distances.shortest_path_len
                           for pawn in self.board.pawns if pawn is not p])
                h = h1 - hh1  # The heuristic value

                # OK h => my minimum distance - minimum one of the player nearest
                # to the goal. So the smallest (NEGATIVE) h the better for ME,
                # If we are in a MIN level

                if MAX:
                    h = -h
                    if h > HH:
                        HH = h
                        result = action

                        if HH >= alpha:
                            HH = alpha
                            stop = True
                elif h < HH:  # MIN
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
            return result, HH, alpha, beta

        # Not a leaf in the search tree. Alpha-Beta minimax
        HH = -INF if MAX else INF
        player = self.board.current_player
        player.distances.push_state()
        r = self.available_actions
        count_r = 0
        L = float(len(r))

        for action in r:
            if not ilevel and player.percent is not None:
                count_r += 1
                player.percent = count_r / L  # [0..1]
                if cfg.__DEBUG__:
                    log('Player %i is thinking: %2.0f%% done.' % (player.id, player.percent * 100))
                self.board.draw_player_info(player.id)

            if isinstance(action, Wall):
                self.board.putWall(action)
                self.pawn.walls -= 1
            else:
                # __DEBUG__
                # print action, ilevel
                i, j = self.pawn.i, self.pawn.j
                self.pawn.move_to(*action)

            self.board.next_player()
            dummy, h, alpha1, beta1 = self.think(not MAX, ilevel + 1, alpha, beta)
            # __DEBUG__
            # print action, '|', dummy, h, '<<<'
            self.previous_player()

            if MAX:
                # __DEBUG__
                # print h, HH
                if h > HH:  # MAX
                    result, HH = action, h
                    if HH >= alpha:
                        HH = alpha
                        stop = True
                    else:
                        beta = HH
            else:
                if h < HH:  # MIN
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
        self.__memoize_think[k] = result, HH, alpha, beta
        # DEBUG__
        # print(result)
        return result, HH, alpha, beta

    @property
    def pawn(self):
        return self.board.current_player

    @property
    def distances(self):
        return self.pawn.distances

    def previous_player(self):
        """ Switches to previous player.
        """
        self.board.player = (self.board.player + self.board.num_players - 1) % self.board.num_players
