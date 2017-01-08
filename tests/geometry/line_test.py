"""Tests the geometry.line module."""
import random

import pytest

from geometry import Line, Point
from geometry.functions import sign


@pytest.mark.flaky(reruns=5)
def test_x_y_and_point_side(first_level, second_level, limit, epsilon):
    """Check that we can calculate the point on a line with a high precision."""
    for _ in range(first_level):
        m = random.uniform(-limit, limit)
        n = random.uniform(-limit, limit)

        x1 = random.uniform(-limit, limit)
        x2 = random.uniform(-limit, limit)
        y1 = m * x1 + n
        y2 = m * x2 + n
        line = Line(Point(x1, y1), Point(x2, y2))

        for _ in range(second_level):
            x = random.uniform(-limit, limit)
            y = m * x + n
            assert -epsilon <= line.x(y) - x <= epsilon
            assert -epsilon <= line.y(x) - y <= epsilon
            assert line.point_side(Point(x, y + epsilon)) == sign(x2 - x1)
