"""Tests the geometry.point module."""

from hypothesis import given

from tests.conftest import points


@given(points, points)
def test_point_relations(p1, p2):
    """Test relation of two points between each other."""
    assert p1.left_of(p2) or p1.x >= p2.x
    assert p1.is_right_of(p2) or p1.x <= p2.x

    assert p1.left_of(p2) == p2.is_right_of(p1) or p1.x == p2.x
    assert not p1.left_of(p2) or not p1.is_right_of(p2)
    assert not p2.left_of(p1) or not p2.is_right_of(p1)
