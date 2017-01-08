"""Defines a triangle class with various helper methods."""
from typing import Tuple, Any, Optional, Union

from .exceptions import ThreePointsAreCollinearException
from .point import Point
from .polygon_helper import Edge
from .polygon_helper import PolygonPoint


class DelaunayTriangle(object):
    """A triangle class."""

    def __init__(self, a: PolygonPoint, b: PolygonPoint, c: PolygonPoint):
        """Create a new triangle consisting of 3 points.

        The points NEED NOT be given in any special order but they MUST NOT be collinear.
        After construction the points of the object are in counter-clockwise order.
        """
        assert isinstance(a, PolygonPoint)
        assert isinstance(b, PolygonPoint)
        assert isinstance(c, PolygonPoint)

        if Point.turn(a, b, c) == Point.NO_TURN:
            raise ThreePointsAreCollinearException()

        if Point.turn(a, b, c) == Point.CCW_TURN:
            self.a = a
            self.b = b
            self.c = c
        else:
            self.a = a
            self.b = c
            self.c = b

        # Make sure the first point is the one with the lowest lexicographic (x, y) pair
        if self.b.tuple() < self.a.tuple() and self.b.tuple() < self.c.tuple():
            self.a, self.b, self.c = self.b, self.c, self.a
        elif self.c.tuple() < self.a.tuple() and self.c.tuple() < self.b.tuple():
            self.a, self.b, self.c = self.c, self.a, self.b
        assert self.a.tuple() < self.b.tuple() and self.a.tuple() < self.c.tuple()

        self.edges = (Edge(self.a, self.b), Edge(self.b, self.c), Edge(self.c, self.a))

    def edges_from(self, edge: Edge) -> Tuple[Edge, Edge, Edge]:
        """O(1): Return edges starting from `edge`."""
        assert isinstance(edge, Edge)
        assert edge in self.edges

        for i in range(3):
            if self.edges[i] == edge:
                return self.edges[i], self.edges[(i + 1) % 3], self.edges[(i + 2) % 3]

    def edges_until(self, edge: Edge) -> Tuple[Edge, Edge, Edge]:
        """O(1): Return edges starting from `edge` omitting `edge` in the result."""
        edges = self.edges_from(edge)
        return edges[1], edges[2], edges[0]

    def contains(self, p: Point) -> bool:
        """O(1): Return whether the triangle contains the given point.

        Args:
            p (Point): The point to check.
        """
        return (Point.turn(self.a, self.b, p) == Point.CCW_TURN and
                Point.turn(self.b, self.c, p) == Point.CCW_TURN and
                Point.turn(self.c, self.a, p) == Point.CCW_TURN)

    def common_edge(self, other: 'DelaunayTriangle') -> Optional[Edge]:
        """O(1): Return the common edge of two triangles. Returns None if both are equal or no common edge exists."""
        if self == other:
            return None

        for edge in self.edges:
            if edge in other.edges:
                return edge

        return None

    @property
    def points(self) -> Tuple[PolygonPoint, PolygonPoint, PolygonPoint]:
        """O(1): Yield all three points."""
        return self.a, self.b, self.c

    def points_as_tuples(self) -> Tuple[
        Tuple[Union[int, float], Union[int, float]], Tuple[Union[int, float], Union[int, float]], Tuple[
            Union[int, float], Union[int, float]]]:
        """O(1): Yield all three points."""
        return self.a.tuple(), self.b.tuple(), self.c.tuple()

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({a!r}, {b!r}, {c!r})'.format(class_=self.__class__.__name__, a=self.a, b=self.b, c=self.c)

    def __eq__(self, other: Any) -> bool:
        """Check for equality with any other object."""
        if isinstance(other, DelaunayTriangle):
            # We can safely just check for equality since the order of points is predetermined (and enforced in the
            # constructor)
            return other.points == self.points

        return False

    def is_at_border(self) -> bool:
        """Check whether this triangle is at the border of the polygon."""
        return (
            abs(self.a.index - self.b.index) == 1 or
            abs(self.a.index - self.c.index) == 1 or
            abs(self.b.index - self.c.index) == 1
        )
