# -*- coding: utf-8 -*-


class CoordMixIn:
    """ Implements a coordinate
    """
    row: int = None
    col: int = None

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
    def __init__(self, row: int, col: int):
        self._row = row
        self._col = col

    def __eq__(self, other: CoordMixIn) -> bool:
        return (self._row, self._col) == (other.row, other.col)

    def __hash__(self):
        return hash((self.row, self.col))

    def __add__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self._row + other.row, self._col + other.col)

    def __sub__(self, other: CoordMixIn) -> CoordMixIn:
        return Coord(self._row - other.row, self._col - other.col)

    def __copy__(self):
        return self.__class__(self._row, self._col)

    def copy(self):
        return self.__copy__()

    @property
    def row(self) -> int:
        return self._row

    @property
    def col(self) -> int:
        return self._col
