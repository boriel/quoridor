# -*- coding: utf-8 -*-

import pygame

from helpers import log
from network.server import EnhancedServer, Functions
import config as cfg
from ai import AI

from .drawable import Drawable
from .pawn import Pawn
from .cell import Cell
from .wall import Wall


class Board(Drawable):
    """ Quoridor board.
    This object contains te state of the game.
    """

    def __init__(self,
                 screen: pygame.Surface,
                 rows=cfg.DEF_ROWS,
                 cols=cfg.DEF_COLS,
                 cell_padding=cfg.CELL_PAD,
                 color=cfg.BOARD_BG_COLOR,
                 border_color=cfg.BOARD_BRD_COLOR,
                 border_size=cfg.BOARD_BRD_SIZE):

        Drawable.__init__(self, screen=screen, color=color, border_color=border_color, border_size=border_size)
        self.rows = rows
        self.cols = cols
        self.cell_pad = cell_padding
        self.mouse_wall = None  # Wall painted on mouse move
        self.player = 0  # Current player 0 or 1
        self.board = []
        self.computing = False  # True if a non-human player is moving

        # Create NETWORK server
        try:
            if cfg.NETWORK_ENABLED:
                self.server = EnhancedServer(("localhost", cfg.PORT))
                log('Network server active at TCP PORT ' + str(cfg.PORT))
                self.server.register_introspection_functions()
                self.server.register_instance(Functions())
                self.server.start()
        except BaseException:
            log('Could not start network server')
            self.server = None

        for i in range(rows):
            self.board += [[]]
            for j in range(cols):
                self.board[-1] += [Cell(screen, self, i, j)]

        self.pawns = []
        self.pawns += [Pawn(screen=screen,
                            board=self,
                            color=cfg.PAWN_A_COL,
                            border_color=cfg.PAWN_BORDER_COL,
                            row=rows - 1,
                            col=cols >> 1  # , # Middle
                            # URL = SERVER_URL + ':%i' % (BASE_PORT + PAWNS)
                            )]
        self.pawns += [Pawn(screen=screen,
                            board=self,
                            color=cfg.PAWN_B_COL,
                            border_color=cfg.PAWN_BORDER_COL,
                            row=0,
                            col=cols >> 1  # Middle
                            )]

        self.regenerate_board(cfg.CELL_COLOR, cfg.CELL_BORDER_COLOR)
        self.num_players = cfg.DEFAULT_NUM_PLAYERS
        self.walls = []  # Walls placed on board
        self.draw_players_info()
        self._AI = []
        # self._AI += [AI(self.pawns[0])]
        self._AI += [AI(self.pawns[1], level=cfg.LEVEL)]

    def regenerate_board(self, c_color, cb_color, c_width=cfg.CELL_WIDTH, c_height=cfg.CELL_HEIGHT):
        """ Regenerate board colors and cell positions.
        Must be called on initialization or whenever a screen attribute
        changes (eg. color, board size, etc)
        """
        y = self.cell_pad
        for i in range(self.rows):
            x = self.cell_pad

            for j in range(self.cols):
                cell = self.board[i][j]
                cell.x, cell.y = x, y
                cell.color = c_color
                cell.border_color = cb_color
                cell.height = c_height
                cell.width = c_width
                cell.pawn = None

                for pawn in self.pawns:
                    if i == pawn.i and j == pawn.j:
                        pawn.cell = cell
                        break

                x += c_width + self.cell_pad

            y += c_height + self.cell_pad

    def draw(self):
        """ Draws a squared n x n board, defaults
        to the standard 9 x 9
        """
        Drawable.draw(self)

        for y in range(self.rows):
            for x in range(self.cols):
                self.board[y][x].draw()

        if cfg.__DEBUG__:
            for p in self.pawns:
                if p.AI:
                    p.distances.draw()
                    break

        for wall in self.walls:
            wall.draw()

    def cell(self, row, col):
        """ Returns board cell at the given
        row and column
        """
        return self.board[row][col]

    def __getitem__(self, i):
        return self.board[i]

    def in_range(self, col, row):
        """ Returns whether te given coordinate are within the board or not
        """
        return 0 <= col < self.cols and 0 <= row < self.rows

    def putWall(self, wall):
        """ Puts the given wall on the board.
        The cells are updated accordingly
        """
        if wall in self.walls:
            return  # If already put, nothing to do

        self.walls += [wall]
        i, j = wall.row, wall.col

        if wall.horiz:
            self.board[i][j].set_path('S', False)
            self.board[i][j + 1].set_path('S', False)
        else:
            self.board[i][j].set_path('W', False)
            self.board[i + 1][j].set_path('W', False)

    def removeWall(self, wall):
        """ Removes a wall from the board.
        The cells are updated accordingly
        """
        if wall not in self.walls:
            return  # Already removed, nothing to do

        self.walls.remove(wall)
        i, j = wall.row, wall.col

        if wall.horiz:
            self.board[i][j].set_path('S', True)
            self.board[i][j + 1].set_path('S', True)
        else:
            self.board[i][j].set_path('W', True)
            self.board[i + 1][j].set_path('W', True)

    def onMouseClick(self, x, y):
        """ Dispatch mouse click Event
        """
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
        """ Get mouse motion event and acts accordingly
        """
        if not self.rect.collidepoint(x, y):
            return

        for row in self.board:
            for cell in row:
                cell.onMouseMotion(x, y)

        if self.which_cell(x, y):
            if self.mouse_wall:
                self.mouse_wall = None
                self.draw()

            return  # The focus was on a cell, we're done

        if not self.current_player.walls:
            return  # The current player has run out of walls. We're done

        wall = self.wall(x, y)
        if not wall:
            return

        if self.can_put_wall(wall):
            self.mouse_wall = wall
            self.draw()
            wall.draw()

    def can_put_wall(self, wall):
        """ Returns whether the given wall can be put
        on the board.
        """
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
        """ Returns which wall is below mouse cursor at x, y coords.
        Returns None if no wall matches x, y coords
        """
        if not self.rect.collidepoint(x, y):
            return None

        # Wall: Guess which top-left cell is it
        j = (x - self.x) // (self.board[0][0].width + self.cell_pad)
        i = (y - self.y) // (self.board[0][0].height + self.cell_pad)
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

        return Wall(self.screen, self, cell.wall_color, i, j, horiz)

    @property
    def x(self):
        """ Absolute left coordinate
        """
        return self.board[0][0].x

    @property
    def y(self):
        """ Absolute left coordinate
        """
        return self.board[0][0].y

    @property
    def width(self):
        return (self.cell_pad + self.board[0][0].width) * self.cols

    @property
    def height(self):
        return (self.cell_pad + self.board[0][0].height) * self.rows

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def next_player(self):
        """ Switches to next player
        """
        self.player = (self.player + 1) % self.num_players
        self.update_pawns_distances()

    def update_pawns_distances(self):
        for pawn in self.pawns:
            pawn.distances.update()

    def which_cell(self, x, y):
        """ Returns an instance of the cell for which (x, y) screen coord
        matches. Otherwise, returns None if no cell is at (x, y) screen
        coords.
        """
        for row in self.board:
            for cell in row:
                if cell.rect.collidepoint(x, y):
                    return cell

        return None

    @property
    def current_player(self):
        """ Returns current player's pawn
        """
        return self.pawns[self.player]

    def draw_player_info(self, player_num):
        """ Draws player pawn at board + padding_offset
        """
        pawn = self.pawns[player_num]
        r = pawn.rect
        r.x = self.rect.x + self.rect.width + cfg.PAWN_PADDING
        r.y = (player_num + 1) * (r.height + cfg.PAWN_PADDING)
        if self.current_player is pawn:
            pygame.draw.rect(self.screen, cfg.CELL_VALID_COLOR, r, 0)
            pygame.draw.rect(self.screen, pawn.border_color, r, 2)
        else:
            pygame.draw.rect(self.screen, self.color, r, 0)

        pawn.draw(r)
        rect = pygame.Rect(r.x + 1, r.y + r.h + 3, cfg.GAUGE_WIDTH, cfg.GAUGE_HEIGHT)

        if pawn.percent is not None:
            pygame.draw.rect(self.screen, cfg.FONT_BG_COLOR, rect, 0)  # Erases old gauge bar
            rect.width = int(cfg.GAUGE_WIDTH * pawn.percent)
            pygame.draw.rect(self.screen, cfg.GAUGE_COLOR, rect, 0)
            rect.width = cfg.GAUGE_WIDTH
            pygame.draw.rect(self.screen, cfg.GAUGE_BORDER_COLOR, rect, 1)
        else:
            pygame.draw.rect(self.screen, cfg.FONT_BG_COLOR, rect, 0)

        r.x += r.width + 20
        r.width = 6
        pygame.draw.rect(self.screen, cfg.WALL_COLOR, r, 0)

        r.x += r.width * 2 + 10
        r.y += r.height // 2 - 5
        r.height = cfg.FONT_SIZE
        r.width *= 3
        pygame.draw.rect(self.screen, cfg.FONT_BG_COLOR, r, 0)  # Erases previous number
        self.msg(r.x, r.y, str(pawn.walls))

        if self.finished and self.current_player == pawn:
            self.msg(r.x + cfg.PAWN_PADDING, r.y, "PLAYER %i WINS!" % (1 + self.player))
            x = self.rect.x
            y = self.rect.y + self.rect.height + cfg.PAWN_PADDING
            self.msg(x, y, "Press any key to EXIT")

    def msg(self, x, y, str_, color=cfg.FONT_COLOR, fsize=cfg.FONT_SIZE):
        font = pygame.font.SysFont(None, fsize)
        fnt = font.render(str_, True, color)
        self.screen.blit(fnt, (x, y))

    def draw_players_info(self):
        """ Calls the above function for every player.
        """
        for i in range(len(self.pawns)):
            self.draw_player_info(i)

    def do_action(self, action):
        """ Performs a playing action: move a pawn or place a barrier.
        Transmit the action to the network, to inform other players.
        """
        player_id = self.current_player.id

        if isinstance(action, Wall):
            wdir = 'horizontal' if action.horiz else 'vertical'
            log('Player %i places %s wall at (%i, %i)' % (player_id, wdir, action.col, action.row))
            self.putWall(action)
            self.current_player.walls -= 1
            net_act = [action.row, action.col, action.horiz]
        else:
            log('Player %i moves to (%i, %i)' % (player_id, action[0], action[1]))
            self.current_player.move_to(*action)
            net_act = list(action)

        for pawn in self.pawns:
            if pawn.is_network_player:
                pawn.NETWORK.do_action(net_act)

    def computer_move(self):
        """ Performs computer moves for every non-human player
        """
        try:
            while self.current_player.AI and not self.finished:
                self.draw()
                self.draw_players_info()
                action, x = self.current_player.AI.move()
                pygame.mixer.music.load('./media/chime.ogg')
                pygame.mixer.music.play()
                self.do_action(action)

                if self.finished:
                    break

                self.next_player()

            self.draw()
            self.draw_players_info()
            self.computing = False

        except AttributeError:
            # This exception is only raised (or should be) on users Break
            pass

    @property
    def finished(self):
        """ Returns whether the match has finished
        or not.
        """
        for pawn in self.pawns:
            if (pawn.i, pawn.j) in pawn.goals:
                return True

        return False

    @property
    def status(self):
        """ Status serialization in a t-uple
        """
        result = str(self.player)

        for p in self.pawns:
            result += p.status

        for i in range(self.rows - 1):
            for j in range(self.cols - 1):
                result += self.board[i][j].status

        return result
