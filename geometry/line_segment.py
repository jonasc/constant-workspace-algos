"""Defines a line segment class with various helper methods."""

import logging
from typing import Union, Optional, Any

from .point import Point


class LineSegment(object):
    """Defines a line segment in R^2."""

    def __init__(self, a: Point, b: Point):
        """Initialize a new line segment given by two points."""
        assert isinstance(a, Point)
        assert isinstance(b, Point)

        self.a = a
        self.b = b

    def reverse(self) -> None:
        """Swap the end points thus reversing the line segment's orientation."""
        self.a, self.b = self.b, self.a

    def intersects(self, other: 'LineSegment') -> bool:
        """Return whether the line segment intersects some other object."""
        if isinstance(other, LineSegment):
            return (
                Point.turn(self.a, self.b, other.a) != Point.turn(self.a, self.b, other.b) and
                Point.turn(other.a, other.b, self.a) != Point.turn(other.a, other.b, self.b)
            )

        raise NotImplementedError()

    def properly_intersects(self, other: 'LineSegment') -> bool:
        """Return whether line segment properly intersects some other object.

        This means touching the line segment does not count as an intersection.
        """
        if isinstance(other, LineSegment):
            turn_other_a = Point.turn(self.a, self.b, other.a)
            turn_other_b = Point.turn(self.a, self.b, other.b)
            turn_self_a = Point.turn(other.a, other.b, self.a)
            turn_self_b = Point.turn(other.a, other.b, self.b)

            return (
                turn_other_a != turn_other_b and
                turn_other_a != Point.NO_TURN and
                turn_other_b != Point.NO_TURN and

                turn_self_a != turn_self_b and
                turn_self_a != Point.NO_TURN and
                turn_self_b != Point.NO_TURN
            )

        raise NotImplementedError()

    def intersection(self, other: 'LineSegment') -> Optional[Point]:
        """Return point at which line segment intersects some other object."""
        if isinstance(other, LineSegment):
            return self._intersection(other, return_point=True)

        raise NotImplementedError()

    def _intersection(self, segm: 'LineSegment', return_point: bool = False) -> Union[bool, Optional[Point]]:
        assert isinstance(segm, LineSegment)
        a1 = self.b.x - self.a.x
        b1 = segm.a.x - segm.b.x
        c1 = segm.a.x - self.a.x
        a2 = self.b.y - self.a.y
        b2 = segm.a.y - segm.b.y
        c2 = segm.a.y - self.a.y

        # TODO, FIXME: Dirty fix, we assume there are no intersecting parallel
        # edges
        if a1 * b2 - a2 * b1 == 0:
            logging.debug('Testing intersection of %s and %s: %s',
                          self, segm, False)
            return False

        s = (c1 * b2 - c2 * b1) / (a1 * b2 - a2 * b1)
        t = (a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)

        logging.debug('Testing intersection of %s and %s: %s (s=%s, t=%s)',
                      self, segm, 0 <= s <= 1 and 0 <= t <= 1, s, t)
        if 0 <= s <= 1 and 0 <= t <= 1:
            if not return_point:
                return True

            if s == 0:
                return self.a
            if s == 1:
                return self.b
            if t == 0:
                return segm.a
            if t == 1:
                return segm.b
            return Point(
                self.a.x + s * a1,
                self.a.y + s * a2,
            )

        if return_point:
            return None
        return False

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({a!r}, {b!r})'.format(class_=self.__class__.__name__, a=self.a, b=self.b)

    def __eq__(self, other: Any) -> bool:
        """Line segments equal if both end-points equal."""
        if isinstance(other, LineSegment):
            return self.a == other.a and self.b == other.b

        raise NotImplementedError()
