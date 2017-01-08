"""Defines a point class with various helper methods."""

import math
from typing import Union, Tuple

from .functions import sign


class Point(object):
    """Defines a point in R^2."""

    CCW_TURN = 1
    NO_TURN = 0
    CW_TURN = -1

    def __init__(self, x: Union[int, float], y: Union[int, float]):
        """Initialize a new point with x and y coordinate."""
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))

        self.x = x
        self.y = y

    def __eq__(self, other: 'Point') -> bool:
        """Check equality of two points."""
        epsilon = 1e-6

        if isinstance(other, Point):
            return (
                -epsilon <= self.x - other.x <= epsilon and
                -epsilon <= self.y - other.y <= epsilon
            )

        raise NotImplementedError()

    def __add__(self, other: 'Point') -> 'Point':
        """Add two points together with component-wise addition."""
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)

        raise NotImplementedError()

    def __sub__(self, other: 'Point') -> 'Point':
        """Subtract other from self with component-wise subtraction."""
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)

        raise NotImplementedError()

    def __mul__(self, other: Union[int, float]) -> 'Point':
        """Multiply all components with a scalar."""
        if isinstance(other, (int, float)):
            return Point(other * self.x, other * self.y)

        raise NotImplementedError()

    def __div__(self, other: Union[int, float]) -> 'Point':
        """Divide all components by a scalar."""
        if isinstance(other, (int, float)):
            return Point(other / self.x, other / self.y)

        raise NotImplementedError()

    def distance_to(self, p: 'Point') -> float:
        """Calculate the distance to another point."""
        assert isinstance(p, Point)

        return math.sqrt(self.squared_distance_to(p))

    def squared_distance_to(self, p: 'Point') -> Union[int, float]:
        """Calculate the squared distance to another point.

        This method can be used if distances only need to be compared and
        therefore calculating the square root can be avoided.
        """
        assert isinstance(p, Point)

        return (self.x - p.x) ** 2 + (self.y - p.y) ** 2

    def is_right_of(self, obj: 'Point') -> bool:
        """Return True if the point is to the right of the other point."""
        if isinstance(obj, Point):
            return obj.x < self.x

        raise NotImplementedError()

    def left_of(self, obj: 'Point') -> bool:
        """Return True if the point is to the left of the other point."""
        if isinstance(obj, Point):
            return obj.x > self.x

        raise NotImplementedError()

    def above(self, obj: 'Point') -> bool:
        """Return True if the point is above the other point."""
        if isinstance(obj, Point):
            return obj.y < self.y

        raise NotImplementedError()

    def below(self, obj: 'Point') -> bool:
        """Return True if the point is below the other point."""
        if isinstance(obj, Point):
            return obj.y > self.y

        raise NotImplementedError()

    @staticmethod
    def turn(p1: 'Point', p2: 'Point', p3: 'Point') -> int:
        """Return the direction of the turn three points form.

        The return value is one of the following:
         1 = left (counterclockwise) turn,
         0 = no turn at all (points are colinear),
        -1 = right (clockwise) turn.
        """
        assert isinstance(p1, Point)
        assert isinstance(p2, Point)
        assert isinstance(p3, Point)

        return sign(
            (p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y)
        )

    def tuple(self) -> Tuple[Union[int, float], Union[int, float]]:
        """Return the coordinates as a tuple."""
        return (self.x, self.y)

    def round(self, digits) -> 'Point':
        """Round both points to the specified number of decimal digits."""
        self.x = round(self.x, digits)
        self.y = round(self.y, digits)
        return self

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({x!r}, {y!r})'.format(class_=self.__class__.__name__, x=self.x, y=self.y)
