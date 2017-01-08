"""Defines a ray class with various helper methods."""
from typing import Optional, Union

from .line import Line
from .line_segment import LineSegment
from .point import Point


class Ray(object):
    """Defines a ray in R^2."""

    def __init__(self, a: Point, b: Point):
        """Initialize a new ray starting at a and going through b."""
        assert isinstance(a, Point)
        assert isinstance(b, Point)

        self.a = a
        self.b = b

    def intersects(self, other: LineSegment) -> bool:
        """Return whether the ray intersects some other object."""
        if isinstance(other, LineSegment):
            turn_other_a = Point.turn(self.a, self.b, other.a)
            turn_other_b = Point.turn(self.a, self.b, other.b)
            if turn_other_a == turn_other_b and turn_other_a != Point.NO_TURN:
                return False
            # TODO: Special case: both are collinear

            turn_self_a = Point.turn(other.a, other.b, self.a)
            turn_self_b = Point.turn(other.a, other.b, self.b)

            # This is the normal line segment intersection case
            if turn_self_a != turn_self_b:
                return True

            # From here on both points of the ray lie on the same side of the
            # line segment
            # We check the orientation of the ray -- the ray and the line
            # segment intersect iff the orientation and the ray points are on
            # different sides of the line segment.
            check_point = other.b + (self.b - self.a)
            check_point_turn = Point.turn(other.a, other.b, check_point)
            return check_point_turn != turn_self_a

        raise NotImplementedError()

    def properly_intersects(self, other: LineSegment) -> bool:
        """Return whether the ray properly intersects some other object."""
        if isinstance(other, LineSegment):
            turn_other_a = Point.turn(self.a, self.b, other.a)
            turn_other_b = Point.turn(self.a, self.b, other.b)
            if turn_other_a == Point.NO_TURN or turn_other_b == Point.NO_TURN:
                return False

            return self.intersects(other)

        raise NotImplementedError()

    def intersection_point(self, segm: Union[LineSegment, Line]) -> Optional[Point]:
        """Return the intersection point of this ray with the given line (segment)."""
        assert isinstance(segm, (LineSegment, Line))

        if self.b == segm.b or self.b == segm.a:
            return self.b
        if self.a == segm.b or self.a == segm.a:
            return self.a

        a1 = self.b.x - self.a.x
        b1 = segm.a.x - segm.b.x
        c1 = segm.a.x - self.a.x
        a2 = self.b.y - self.a.y
        b2 = segm.a.y - segm.b.y
        c2 = segm.a.y - self.a.y

        # TODO, FIXME: Dirty fix, we assume there are no intersecting parallel
        # edges
        if a1 * b2 - a2 * b1 == 0:
            return None

        s = (c1 * b2 - c2 * b1) / (a1 * b2 - a2 * b1)
        t = (a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)

        if s == 0:
            return self.a
        if s == 1:
            return self.b
        if t == 0:
            return segm.a
        if t == 1:
            return segm.b

        # Intersection lies on the wrong side of the ray
        if s < 0:
            return None

        # Intersection lies outside of line segment
        if isinstance(segm, LineSegment) and (t < 0 or t > 1):
            return None

        return Point(
            self.a.x + s * a1,
            self.a.y + s * a2,
        )

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({a!r}, {b!r})'.format(class_=self.__class__.__name__, a=self.a, b=self.b)
