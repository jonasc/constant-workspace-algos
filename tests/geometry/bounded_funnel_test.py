"""Tests the geometry.bounded_funnel module."""

from geometry import BoundedFunnel, LineSegment, Point


def line_segment(x1, y1, x2, y2):
    """Create a line segment from four points."""
    return LineSegment(Point(x1, y1), Point(x2, y2))


def funnel():
    """Create a specific funnel."""
    return BoundedFunnel(Point(3, 0), Point(6, 6), Point(0, 6), Point(6, 4), Point(2, 4))


def test_funnel_division():
    """Test whether a funnel is divided by various line segments."""
    f = funnel()

    ls = line_segment(5, 3, 1, 3)

    assert f.is_divided_by(ls)
    assert f.is_properly_divided_by(ls)
    assert f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 1, 1, 5)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(0, 2, 2, 5)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(1, 2, 4, 5)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(1, 2, 3, 6)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 1, 1, 4)

    assert f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 3, 1, 4)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 2, 2, 2)

    assert f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 4, 2, 4)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(4, 2, 1, 4)

    assert f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)

    ls = line_segment(7, 4, 0, 4)

    assert not f.is_divided_by(ls)
    assert not f.is_properly_divided_by(ls)
    assert not f.is_half_properly_divided_by(ls)
