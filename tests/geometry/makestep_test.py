"""Check some functions from the makestep algorithm."""
from geometry import EdgePoint, Point, Polygon, PolygonPoint
from gsp.makestep import hit_polygon_boundary, in_subpolygon


def start_1():
    """Generate a start configuration."""
    polygon = Polygon([Point(x, y) for x, y in ((0, 2), (10, 0), (3, 2), (9, 1), (8, 8), (5, 3), (4.5, 5), (4, 6))])
    t = Point(4.25, 5.25)
    t_trapezoid = polygon.trapezoid(t)
    p = PolygonPoint(7.5, 4)
    q1 = polygon.point(5)
    q2 = hit_polygon_boundary(p, q1, polygon)

    assert isinstance(q2, EdgePoint) and q2.index == 0

    return polygon, q1, q2, t, t_trapezoid


def test_in_subpolygon_1():
    """Test the in_subpolygon function."""
    polygon, q1, q2, t, t_trapezoid = start_1()

    assert in_subpolygon(polygon, q1, q2, t, t_trapezoid)


def test_in_subpolygon_2():
    """Test the in_subpolygon function."""
    polygon, q1, q2, t, t_trapezoid = start_1()

    assert not in_subpolygon(polygon, q2, q1, t, t_trapezoid)
