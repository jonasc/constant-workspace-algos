"""Defines a circle class with various helper methods."""

import math

from .exceptions import ThreePointsAreCollinearException
from .point import Point


class Circle(object):
    """Defines a circle in R^2."""

    def __init__(self, *args, squared: bool = False):
        """Initialize a new circle.

        The circle can be given either as three (non-colinear) points or as a
        point an a (potentially squared) radius.
        """
        if len(args) == 3:
            assert isinstance(args[0], Point)
            assert isinstance(args[1], Point)
            assert isinstance(args[2], Point)

            a, b, c = args

            # Calculate first perpendicular bisector
            if a.y == b.y:
                bisector1 = (1, 0, (a.x + b.x) / 2)
            else:
                bisector1 = (
                    2 * (a.x - b.x),
                    2 * (a.y - b.y),
                    a.x ** 2 - b.x ** 2 + a.y ** 2 - b.y ** 2
                )

            # Calculate second perpendicular bisector
            if a.y == c.y:
                bisector2 = (1, 0, (a.x + c.x) / 2)
            else:
                bisector2 = (
                    2 * (a.x - c.x),
                    2 * (a.y - c.y),
                    a.x ** 2 - c.x ** 2 + a.y ** 2 - c.y ** 2
                )

            # Raise exception if both bisectors are parallel and thus the three
            # points are colinear
            if bisector1[1] * bisector2[0] == bisector1[0] * bisector2[1]:
                raise ThreePointsAreCollinearException()

            # Calculate the circumcirle's center
            self.center = Point(
                (bisector1[2] * bisector2[1] - bisector2[2] * bisector1[1]) /
                (bisector1[0] * bisector2[1] - bisector2[0] * bisector1[1]),
                (bisector1[0] * bisector2[2] - bisector2[0] * bisector1[2]) /
                (bisector1[0] * bisector2[1] - bisector2[0] * bisector1[1]),
            )

            self._radius2 = self.center.squared_distance_to(args[0])
            self._radius = None

        elif len(args) == 2:
            assert isinstance(args[0], Point)
            assert isinstance(args[1], (int, float))

            self.center = args[0]
            if squared:
                self._radius2 = args[1]
                self._radius = None
            else:
                self._radius = args[1]
                self._radius2 = None

        else:
            raise NotImplementedError()

    @property
    def radius(self) -> float:
        """Return the radius of the circle."""
        if self._radius is None:
            self._radius = math.sqrt(self._radius2)
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        """Set the radius of the circle."""
        assert isinstance(value, (int, float))

        self._radius = value
        self._radius2 = None

    @property
    def radius2(self) -> float:
        """Return the squared radius of the circle."""
        if self._radius2 is None:
            self._radius2 = self._radius * self._radius
        return self._radius2

    @radius2.setter
    def radius2(self, value: float) -> None:
        """Set the squared radius of the circle."""
        assert isinstance(value, (int, float))

        self._radius2 = value
        self._radius = None

    def contains(self, p: Point) -> bool:
        """Check whether the circle contains the given point."""
        assert isinstance(p, Point)

        return self.center.squared_distance_to(p) <= self.radius2

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({center!r}, {radius!r}, squared=True)'.format(class_=self.__class__.__name__,
                                                                       center=self.center, radius=self.radius2)
