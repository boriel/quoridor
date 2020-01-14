# -*- coding: utf-8 -*-

from abc import ABC
from entities.wall import Wall
from entities.coord import Coord


class Action(ABC):
    """ Describes an action in the game (place a wall or move pawn)
    """


class ActionPlaceWall(Action):
    """ This action describes placing a wall
    """
    def __init__(self, wall: Wall):
        self.wall = wall

    def __repr__(self):
        return 'PlaceWall<{}>'.format(self.wall)


class ActionMovePawn(Action):
    """ This action describes moving a pawn from_ a cord to_ another one
    """
    def __init__(self, from_: Coord, to_: Coord):
        self.orig = from_
        self.dest = to_

    def __repr__(self):
        return 'Move{{{} -> {}}}>'.format(self.orig, self.dest)
