"""Test triangulated polygons."""

from hypothesis import example, given

from geometry import Point, Polygon, TriangulatedPolygon
from tests.conftest import polygons


@given(polygons)
@example(Polygon((Point(0.0, 0.0), Point(0.0, 1.0000000000000003e-30),
                  Point(1.0000000000000003e-30, 1.0000000000000003e-30), Point(1.0000000000000003e-30, 0.0))))
@example(Polygon((Point(0, 1), Point(1, 0), Point(0, 2), Point(-1, 0))))
def test_triangulation(polygon):
    """Test length and content of triangulation."""
    polygon = TriangulatedPolygon(polygon)
    # Make sure there are exactly n-2 triangles
    assert len(polygon.triangles) + 2 == len(polygon.points)

    # Make sure no two triangles are the same
    for i, t_i in enumerate(polygon.triangles):
        for j, t_j in enumerate(polygon.triangles):
            assert t_i != t_j or i == j


@given(polygons)
def test_polygon_equality(polygon):
    """Check that a polygon and a triangulated version of it are the same."""
    triangulated_polygon = TriangulatedPolygon(polygon)

    assert polygon == triangulated_polygon
