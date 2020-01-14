# -*- coding: utf-8 -*-


class CoordMixIn:
    """ Implements a coordinate
    """
    row: int = None
    col: int = None

    def __hash__(self):
        return hash((self.row, self.col))

    def __repr__(self):
        return '{}<{}, {}>'.format(self.__class__.__name__, self.row, self.col)

    def __len__(self):
        return 2

    def __getitem__(self, item):
        return (self.row, self.col)[item]

    def __copy__(self):
        result = self.__class__()
        result.row, result.col = self.row, self.col
        return result


class Coord(CoordMixIn):
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def __eq__(self, other: CoordMixIn) -> bool:
        return (self.row, self.col) == (other.row, other.col)

    def __add__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self.row + other.row, self.col + other.col)

    def __iadd__(self, other: CoordMixIn):
        self.row += other.row
        self.col += other.col

    def __sub__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self.row - other.row, self.col - other.col)

    def __isub__(self, other: CoordMixIn):
        self.row -= other.row
        self.col -= other.col

    def __copy__(self):
        return self.__class__(self.row, self.col)

    def copy(self) -> CoordMixIn:
        return self.__copy__()
