"""Tests the geometry.circle module."""

from hypothesis import assume, given

from geometry import Circle, Point
from tests.conftest import points


@given(points, points, points)
def test_can_create_circle(p1, p2, p3):
    """Check that we can always create a circle if the points do not lie on one line."""
    assume(Point.turn(p1, p2, p3) != Point.NO_TURN)
    Circle(p1, p2, p3)
