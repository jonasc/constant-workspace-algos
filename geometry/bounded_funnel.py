"""Defines a funnel class with helper methods."""
from typing import Union

from .exceptions import BoundedFunnelMustNotBeConcaveException
from .funnel import Funnel
from .line import Line
from .line_segment import LineSegment
from .point import Point


class BoundedFunnel(Funnel):
    """Defines a bounded funnel (an angular region defined by three points and two boundary points) in R^2."""

    BEHIND = 3

    def __init__(self, cusp: Point, first: Point, second: Point, boundary_a: Point, boundary_b: Point):
        """Create a new funnel."""
        assert isinstance(boundary_a, Point)
        assert isinstance(boundary_b, Point)

        super(BoundedFunnel, self).__init__(cusp, first, second)

        if self._type == Funnel._CONCAVE:
            raise BoundedFunnelMustNotBeConcaveException('Bounded funnel must not be concave.')

        self.boundary_a = boundary_a
        self.boundary_b = boundary_b
        self.boundary = Line(self.boundary_a, self.boundary_b)

        if Point.turn(boundary_a, boundary_b, cusp) == Point.CW_TURN:
            raise ValueError('Bounding line segment needs to be aligned in a counterclockwise way.')

        self._vertex_a = None
        self._vertex_b = None

    @property
    def first_vertex(self) -> Point:
        """Return the intersection of the ray bounding the funnel on the right side and the boundary."""
        if self._vertex_a is None:
            self._vertex_a = self.first_ray.intersection_point(self.boundary)
        return self._vertex_a

    @property
    def second_vertex(self) -> Point:
        """Return the intersection of the ray bounding the funnel on the left side and the boundary."""
        if self._vertex_b is None:
            self._vertex_b = self.second_ray.intersection_point(self.boundary)
        return self._vertex_b

    @Funnel.first.setter
    def first(self, value: Point) -> None:
        """Delete the cached value for self.first_vertex when setting the new ray point."""
        super(BoundedFunnel, self.__class__).first.__set__(self, value)
        self._vertex_a = None

    @Funnel.second.setter
    def second(self, value: Point) -> None:
        """Delete the cached value for self.first_vertex when setting the new ray point."""
        super(BoundedFunnel, self.__class__).second.__set__(self, value)
        self._vertex_b = None

    def contains(self, other: Union[Point, LineSegment]):
        """Check whether the funnel contains other."""
        if isinstance(other, Point):
            return (
                super(BoundedFunnel, self).contains(other) and
                Point.turn(self.boundary_a, self.boundary_b, other) != Point.CW_TURN
            )

        if isinstance(other, LineSegment):
            return self.contains(other.a) and self.contains(other.b)

        raise TypeError()

    def properly_contains(self, other: Union[Point, LineSegment]):
        """Check whether funnel contains other without touching the boundary."""
        if isinstance(other, Point):
            return (
                super(BoundedFunnel, self).properly_contains(other) and
                Point.turn(self.boundary_a, self.boundary_b, other) == Point.CCW_TURN
            )

        if isinstance(other, LineSegment):
            return self.properly_contains(other.a) and self.properly_contains(other.b)

        raise TypeError()

    def intersects(self, other: LineSegment):
        """Check whether the funnel intersects other."""
        if isinstance(other, LineSegment):
            # TODO: This might be more complex -- because for non-proper containment both endpoints can lie on the edge
            return (
                (self.contains(other.a) and not self.contains(other.b)) or
                (self.contains(other.b) and not self.contains(other.a))
            )

        raise TypeError()

    def properly_intersects(self, other: LineSegment):
        """Check whether the funnel intersects other."""
        if isinstance(other, LineSegment):
            return (
                (self.properly_contains(other.a) and not self.contains(other.b)) or
                (self.properly_contains(other.b) and not self.contains(other.a))
            )

        raise TypeError()

    def is_divided_by(self, other: LineSegment):
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            turn_a = Point.turn(self.first_vertex, self.second_vertex, other.a)
            turn_b = Point.turn(self.first_vertex, self.second_vertex, other.b)

            if turn_a == turn_b == Point.NO_TURN:
                return False

            return (
                self.first_ray.intersects(other) and self.second_ray.intersects(other) and
                turn_a != Point.CW_TURN and
                turn_b != Point.CW_TURN
            )

        raise TypeError()

    def is_properly_divided_by(self, other: LineSegment) -> bool:
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            if not (self.first_ray.properly_intersects(other) and self.second_ray.properly_intersects(other)):
                return False

            oa, ob = other.a, other.b
            if Point.turn(self.cusp, oa, ob) == Point.CW_TURN:
                oa, ob = ob, oa

            return (
                Point.turn(oa, ob, self.first_vertex) == Point.CW_TURN and
                Point.turn(oa, ob, self.second_vertex) == Point.CW_TURN
            )

        raise TypeError()

    def is_half_properly_divided_by(self, other: LineSegment) -> bool:
        """Check whether other completely divides the funnel into two parts."""
        if isinstance(other, LineSegment):
            if Point.turn(other.a, other.b, self.boundary_a) == Point.turn(other.a, other.b, self.boundary_b) == \
                    Point.NO_TURN:
                return False

            oa, ob = other.a, other.b
            if Point.turn(self.cusp, oa, ob) == Point.CW_TURN:
                oa, ob = ob, oa
            turn_a = Point.turn(oa, ob, self.first_vertex)
            turn_b = Point.turn(oa, ob, self.second_vertex)

            # If one of the two boundary points lies to the left of our line segment, the line segment does not shadow
            if turn_a == Point.CCW_TURN or turn_b == Point.CCW_TURN or turn_a == turn_b == Point.NO_TURN:
                return False

            return (
                (self.first_ray.properly_intersects(other) and self.second_ray.intersects(other)) or
                (self.first_ray.intersects(other) and self.second_ray.properly_intersects(other))
            )

        raise TypeError()

    def position_of(self, p: Point) -> int:
        """Return where the point p is relative to the funnel.

        The returned value is one of Funnel.INSIDE, Funnel.LEFT_OF,
        Funnel.RIGHT_OF, Funnel.OPPOSITE and BoundedFunnel.BEHIND.
        If a point lies on the funnel boundary it is considered INSIDE.
        Additionally if it lies on the extension of one of the funnel rays to
        the other side it is considered to be OPPOSITE.
        """
        assert isinstance(p, Point)

        first_turn = Point.turn(self.cusp, self._first, p)
        second_turn = Point.turn(self.cusp, self._second, p)
        boundary_turn = Point.turn(self.boundary_a, self.boundary_b, p)

        # Case 1: point lies inside funnel
        if first_turn != Point.CW_TURN and second_turn != Point.CCW_TURN:
            # Now decide whether it lies before or behind the boundary
            if boundary_turn != Point.CW_TURN:
                return Funnel.INSIDE
            return BoundedFunnel.BEHIND

        # Case 2: point lies on the opposite site of the funnel
        if first_turn != Point.CCW_TURN and second_turn != Point.CW_TURN:
            return Funnel.OPPOSITE

        # Case 3: We can safely return of of the two turns since now they are
        # both the same and since Funnel.LEFT_OF == Point.CCW_TURN and
        # Funnel.RIGHT_OF == Point.CW_TURN.
        return first_turn

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return (
            '{class_}(cusp={cusp!r}, first={first!r}, second={second!r}, boundary_a={boundary_a!r}, boundary_b={'
            'boundary_b!r})').format(
                class_=self.__class__.__name__, cusp=self.cusp, first=self._first, second=self._second,
                boundary_a=self.boundary_a, boundary_b=self.boundary_b)
