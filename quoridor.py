#!/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
from pygame import Color
import threading
import argparse

from helpers import log
import config as cfg
import core
from network.server import EnhancedServer

from entities.board import Board


def dispatch(events, board: Board):
    for event in events:
        if event.type == QUIT:
            return False

        if hasattr(event, 'key'):
            if event.key == K_ESCAPE or board.finished:
                return False

        if board.computing or board.finished or board.current_player.is_network_player:
            continue

        if event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            board.onMouseClick(x, y)

        if event.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            board.onMouseMotion(x, y)

    return True


def main() -> int:
    core.init()

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", dest="level",
                        help="AI player Level. Default is 0 (Easy). Higher is harder)",
                        default=cfg.LEVEL, type=int)

    options = parser.parse_args()
    cfg.LEVEL = options.level

    log('Quoridor AI game, (C) 2009 by Jose Rodriguez (a.k.a. Boriel)')
    log('This program is Free')
    log('Initializing system...')

    pygame.init()
    clock = pygame.time.Clock()
    pygame.display.set_mode((800, 600))
    pygame.display.set_caption(cfg.GAME_TITLE)
    screen = pygame.display.get_surface()

    screen.fill(Color(255, 255, 255))
    board = core.BOARD = Board(screen)
    board.draw()
    log('System initialized OK')

    cont = True
    while cont:
        clock.tick(cfg.FRAMERATE)
        pygame.display.flip()

        if not board.computing and not board.finished:
            if board.current_player.AI:
                board.computing = True
                thread = threading.Thread(target=board.computer_move)
                thread.start()

        cont = dispatch(pygame.event.get(), board)

    del board.rows

    pygame.quit()
    if cfg.NETWORK_ENABLED:
        EnhancedServer.terminate_server()

    log('Memoized nodes: %i' % core.MEMOIZED_NODES)
    log('Memoized nodes hits: %i' % core.MEMOIZED_NODES_HITS)

    for pawn in board.pawns:
        log('Memoized distances for [%i]: %i' % (pawn.id, pawn.distances.MEMO_COUNT))
        log('Memoized distances hits for [%i]: %i' % (pawn.id, pawn.distances.MEMO_HITS))

    log('Exiting. Bye!')
    return 0


if __name__ == '__main__':
    main()
