"""Defines a polygon class with various helper classes and methods."""

from typing import Iterable, Union

from triangle import triangulate

from geometry import Polygon
from .delaunay_triangle import DelaunayTriangle
from .point import Point


class TriangulatedPolygonTriangle(DelaunayTriangle):
    """A 2D triangle with neighbours."""

    def __init__(self, a: Point, b: Point, c: Point):
        """Create a new triangle."""
        super(TriangulatedPolygonTriangle, self).__init__(a, b, c)

        self.neighbour_indices = []


class TriangulatedPolygon(Polygon):
    """Defines a polygon in R^2 together with it's triangulation."""

    def __init__(self, points: Union[Iterable[Point], Polygon]):
        """O(n^3): Initialize a new polygon with a list of points.

        The list can be anything which ist convertible to a list when passed to
        the builtin list function. It is furthermore assumed that all objects in
        this list are Point instances.

        We also assume that the points are given in counterclockwise order.
        Otherwise the names of some functions do not make sense.
        """
        super(TriangulatedPolygon, self).__init__(points)

        self._triangulate()

    def _triangulate(self):
        """O(n^3): Triangulate the polygon."""
        data = dict(
            vertices=list(self.points_as_tuples()),
            segments=[(i, (i + 1) % len(self)) for i in range(len(self))],
        )
        result = triangulate(data, 'p')

        mapping = dict()
        self.triangles = []

        for triple in result['triangles']:
            triangle = TriangulatedPolygonTriangle(*map(self.points.__getitem__, triple))
            self.triangles.append(triangle)
            for edge in triangle.edges:
                fst, snd = edge.a.index, edge.b.index
                if snd < fst:
                    fst, snd = snd, fst
                if (fst, snd) in mapping:
                    self.triangles[mapping[(fst, snd)]].neighbour_indices.append(len(self.triangles) - 1)
                    triangle.neighbour_indices.append(mapping[(fst, snd)])
                else:
                    mapping[(fst, snd)] = len(self.triangles) - 1

    def locate_point_in_triangle(self, p: Point) -> TriangulatedPolygonTriangle:
        """O(n): Find triangle in which p is located."""
        for triangle in self.triangles:
            if triangle.contains(p):
                return triangle

        raise ValueError()

    def point_inside_at(self, index: int, round: bool = True) -> Point:
        """O(n): Return a point that lies inside the polygon near the given edge.

        Args:
            index: The index of the edge at which the point should be located.

        Returns:
            Point: A point inside the polygon near the edge with the given index.
        """
        for t in self.triangles:
            if (index in (t.a.index, t.b.index, t.c.index) and
                    (index + 1) % len(self) in (t.a.index, t.b.index, t.c.index)):
                break
        else:
            assert False

        p = Point((t.a.x + t.b.x + t.c.x) / 3, (t.a.y + t.b.y + t.c.y) / 3)

        if not round:
            return p

        q = None
        digits = 4
        triangle = DelaunayTriangle(t.a, t.b, t.c)

        while q is None or not triangle.contains(q):
            q = Point(p.x, p.y).round(digits)
            digits += 1

        return q
