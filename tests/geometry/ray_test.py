"""Tests the geometry.ray module."""

import random

from geometry import Point, LineSegment, Ray


def test_ray_intersection():
    """Check for intersection of a ray with line segments."""
    ray = Ray(Point(0, 0), Point(1, 1))

    line_segment_1 = LineSegment(Point(5, 5), Point(4, 6))
    assert ray.intersects(line_segment_1)
    assert not ray.properly_intersects(line_segment_1)

    line_segment_2 = LineSegment(Point(1, 2), Point(2, 1))
    assert ray.intersects(line_segment_2)
    assert ray.properly_intersects(line_segment_2)

    line_segment_3 = LineSegment(Point(2, 1), Point(4, 2))
    assert not ray.intersects(line_segment_3)
    assert not ray.properly_intersects(line_segment_3)


def test_ray_intersection_implications(first_level, second_level, limit):
    """Check for intersection of a ray with line segments and its implications."""
    for _ in range(first_level):
        ray = Ray(Point(random.uniform(-limit, limit), random.uniform(-limit, limit)),
                  Point(random.uniform(-limit, limit), random.uniform(-limit, limit)))

        for _ in range(second_level):
            line_segment = LineSegment(Point(random.uniform(-limit, limit), random.uniform(-limit, limit)),
                                       Point(random.uniform(-limit, limit), random.uniform(-limit, limit)))

            assert (not ray.properly_intersects(line_segment)) or (ray.intersects(line_segment))
