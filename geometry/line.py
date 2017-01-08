"""Defines a line class with various helper methods."""
from typing import Union

from .exceptions import DegeneratedCaseException
from .point import Point


class Line(object):
    """Defines a line in R^2."""

    def __init__(self, a: Point, b: Point):
        """Initialize a new line going through two points."""
        assert isinstance(a, Point)
        assert isinstance(b, Point)

        if a == b:
            raise DegeneratedCaseException()

        self.a = a
        self.b = b

    @staticmethod
    def x_value(a: Point, b: Point, y: Union[int, float]) -> float:
        """Return the x coordinate on a line (a, b) to a given y coordinate."""
        assert isinstance(y, (int, float))

        if a.y == b.y:
            raise ValueError('Cannot return x-value for y=const.')

        return (a.x - b.x) * (y - b.y) / (a.y - b.y) + b.x

    def x(self, y: Union[int, float]) -> float:
        """Return the x coordinate to a given y coordinate."""
        return Line.x_value(self.a, self.b, y)

    @staticmethod
    def y_value(a: Point, b: Point, x: Union[int, float]) -> float:
        """Return the y coordinate on a line (a, b) to a given x coordinate."""
        assert isinstance(x, (int, float))

        if a.x == b.x:
            raise ValueError('Cannot return y-value for x=const.')

        return (a.y - b.y) * (x - b.x) / (a.x - b.x) + b.y

    def y(self, x: Union[int, float]) -> float:
        """Return the y coordinate to a given x coordinate."""
        return Line.y_value(self.a, self.b, x)

    def point_side(self, p: Point) -> int:
        """Return the position of the point relative to the line.

        The line's direction is from its first to its second point. The result
        is one of the following:
         1 = on the left,
         0 = on the line,
        -1 = on the right.
        """
        assert isinstance(p, Point)

        return Point.turn(self.a, self.b, p)

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({a!r}, {b!r})'.format(class_=self.__class__.__name__, a=self.a, b=self.b)

    def __eq__(self, other):
        """Cannot compare lines (at least I don't need it right now)."""
        raise NotImplementedError()
