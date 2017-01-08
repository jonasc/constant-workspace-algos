"""Defines a funnel class with helper methods."""
from typing import Union

from .line_segment import LineSegment
from .point import Point
from .ray import Ray


class Funnel(object):
    """Defines a funnel (an angular region defined by three points) in R^2."""

    INSIDE = 0
    LEFT_OF = 1
    RIGHT_OF = -1
    OPPOSITE = 2

    _CONVEX = 1
    _NEITHER = 0
    _CONCAVE = -1

    def __init__(self, cusp: Point, first: Point, second: Point):
        """Initialize a new funnel given by three points."""
        assert isinstance(cusp, Point)
        assert isinstance(first, Point)
        assert isinstance(second, Point)

        self._cusp = cusp
        self._first = first
        self._second = second

        self._first_ray = None
        self._second_ray = None

        self._type = Point.turn(cusp, first, second)

    @property
    def first(self) -> Point:
        """Return the first boundary point."""
        return self._first

    @first.setter
    def first(self, value: Point) -> None:
        """Set the first boundary point."""
        assert isinstance(value, Point)

        self._first = value
        self._first_ray = None
        self._type = Point.turn(self.cusp, self.first, self.second)

    @property
    def cusp(self) -> Point:
        """Return the cusp."""
        return self._cusp

    @cusp.setter
    def cusp(self, value: Point) -> None:
        """Set the cusp boundary point."""
        assert isinstance(value, Point)

        self._cusp = value
        self._type = Point.turn(self.cusp, self.first, self.second)
        self._first_ray = None
        self._second_ray = None

    @property
    def second(self) -> Point:
        """Return the second boundary point."""
        return self._second

    @second.setter
    def second(self, value: Point) -> None:
        """Set the second boundary point."""
        assert isinstance(value, Point)

        self._second = value
        self._second_ray = None
        self._type = Point.turn(self.cusp, self.first, self.second)

    @property
    def first_ray(self) -> Ray:
        """Return the ray through our first point."""
        if self._first_ray is None:
            self._first_ray = Ray(self.cusp, self._first)
        return self._first_ray

    @property
    def second_ray(self) -> Ray:
        """Return the ray through our second point."""
        if self._second_ray is None:
            self._second_ray = Ray(self.cusp, self._second)
        return self._second_ray

    def contains(self, other: Union[Point, LineSegment]) -> bool:
        """Check whether the funnel contains other."""
        if isinstance(other, Point):
            if self._type == Funnel._CONCAVE:
                return not (
                    Point.turn(self.cusp, self._first, other) == Point.CW_TURN and
                    Point.turn(self.cusp, self._second, other) == Point.CCW_TURN
                )
            else:
                return (
                    Point.turn(self.cusp, self._first, other) != Point.CW_TURN and
                    Point.turn(self.cusp, self._second, other) != Point.CCW_TURN
                )

        if isinstance(other, LineSegment):
            if self._type == Funnel._CONCAVE:
                # If the funnel is concave both line segment endpoints can lie inside the funnel but still cross
                # the funnel boundaries
                return (
                    self.contains(other.a) and self.contains(other.b) and
                    not self.first_ray.properly_intersects(other)
                )
            else:
                return self.contains(other.a) and self.contains(other.b)

        raise NotImplementedError()

    def properly_contains(self, other: Union[Point, LineSegment]) -> bool:
        """Check whether funnel contains other without touching the boundary."""
        if isinstance(other, Point):
            if self._type == Funnel._CONCAVE:
                return not (
                    Point.turn(self.cusp, self._first, other) != Point.CCW_TURN and
                    Point.turn(self.cusp, self._second, other) != Point.CW_TURN
                )
            else:
                return (
                    Point.turn(self.cusp, self._first, other) == Point.CCW_TURN and
                    Point.turn(self.cusp, self._second, other) == Point.CW_TURN
                )

        if isinstance(other, LineSegment):
            return (
                self.properly_contains(other.a) and
                self.properly_contains(other.b) and
                not self.first_ray.intersects(other) and
                not self.second_ray.intersects(other)
            )

        raise NotImplementedError()

    def intersects(self, other: LineSegment) -> bool:
        """Check whether the funnel intersects other."""
        if isinstance(other, LineSegment):
            return self.first_ray.intersects(other) or self.second_ray.intersects(other)

        raise NotImplementedError()

    def properly_intersects(self, other: LineSegment) -> bool:
        """Check whether the funnel properly intersects other."""
        if isinstance(other, LineSegment):
            return self.first_ray.properly_intersects(other) or self.second_ray.properly_intersects(other)

        raise NotImplementedError()

    def is_divided_by(self, other: LineSegment) -> bool:
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            return self.first_ray.intersects(other) and self.second_ray.intersects(other)

        raise NotImplementedError()

    def is_properly_divided_by(self, other: LineSegment) -> bool:
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            return self.first_ray.properly_intersects(other) and self.second_ray.properly_intersects(other)

        raise NotImplementedError()

    def is_half_properly_divided_by(self, other: LineSegment) -> bool:
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            return (
                (self.first_ray.properly_intersects(other) and self.second_ray.intersects(other)) or
                (self.first_ray.intersects(other) and self.second_ray.properly_intersects(other))
            )

        raise NotImplementedError()

    def position_of(self, p: Point) -> int:
        """Return where the point p is relative to the funnel.

        The returned value is one of Funnel.INSIDE, Funnel.LEFT_OF,
        Funnel.RIGHT_OF and Funnel.OPPOSITE.
        If a point lies on the funnel boundary it is considered INSIDE.
        Additionally if it lies on the extension of one of the funnel rays to
        the other side it is considered to be OPPOSITE.
        """
        assert isinstance(p, Point)

        # Concave funnels are special -- there is just INSIDE and OPPOSITE
        if self._type == Funnel._CONCAVE:
            if self.contains(p):
                return Funnel.INSIDE
            return Funnel.OPPOSITE

        first_turn = Point.turn(self.cusp, self._first, p)
        second_turn = Point.turn(self.cusp, self._second, p)

        # Case 1: point lies inside funnel
        if first_turn != Point.CW_TURN and second_turn != Point.CCW_TURN:
            return Funnel.INSIDE

        # Case 2: point lies on the opposite site of the funnel
        if first_turn != Point.CCW_TURN and second_turn != Point.CW_TURN:
            return Funnel.OPPOSITE

        # Case 3: We can safely return of of the two turns since now they are
        # both the same and since Funnel.LEFT_OF == Point.CCW_TURN and
        # Funnel.RIGHT_OF == Point.CW_TURN.
        return first_turn

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}(cusp={cusp!r}, first={first!r}, second={second!r})'.format(class_=self.__class__.__name__,
                                                                                    cusp=self.cusp, first=self._first,
                                                                                    second=self._second)
