# -*- coding: utf-8 -*-


class CoordMixIn:
    """ Implements a coordinate
    """
    __slots__ = 'row', 'col'

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
    """ Coordinate (immutable) object (row, col).
    """
    __slots__ = '_hash'

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self._hash = hash((self.row, self.col))

    def __eq__(self, other: CoordMixIn) -> bool:
        return (self.row, self.col) == (other.row, other.col)

    def __hash__(self):
        return self._hash

    def __add__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self.row + other.row, self.col + other.col)

    def __sub__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self.row - other.row, self.col - other.col)

    def __copy__(self):
        return self.__class__(self.row, self.col)

    def copy(self):
        return self.__copy__()
