"""Various functions to create specifiy polygons."""

import functools
from collections import deque
from math import cos, exp, log, pi, sin
from random import uniform
from typing import Union

from benchmark import model
from geometry import Point, Polygon, TriangulatedPolygon


def polygon(func):
    """Allow decorated functions to just return a list of points and not care about polygon types."""
    @functools.wraps(func)
    def wrapper(*args, triangulated: bool = False, **kwargs):
        points = func(*args, **kwargs)
        if triangulated:
            return TriangulatedPolygon(points)
        else:
            return Polygon(points)

    return wrapper


@polygon
def star_polygon(n: int, small_radius: float, big_radius: float, round: int = 4) -> Union[Polygon, TriangulatedPolygon]:
    """A star shaped polygon with the points evenly distributed on an inner and an outer circle."""
    if n % 2 == 1:
        raise ValueError('Number of vertices MUST be a multiple of 2.')
    if n < 4:
        raise ValueError('Number of vertices MUST be at least 4.')

    if not (0 < small_radius < big_radius):
        raise ValueError('This MUST hold: 0 < small_radius < big_radius.')

    perturbation = 2 * pi * small_radius / n * 0.1

    points = []
    for i in range(n):
        radius = small_radius if i % 2 == 0 else big_radius
        points.append(Point(radius * cos(2 * pi * i / n) + uniform(-perturbation, perturbation),
                            radius * sin(2 * pi * i / n) + uniform(-perturbation, perturbation)).round(4))

    return points


@polygon
def concave_triangle(n: int, width: float, height: float, inner_height: float = None, round: int = 4
                     ) -> Union[Polygon, TriangulatedPolygon]:
    """A concave triangle with one point at the top and many points on the bottom."""
    if n < 4:
        raise ValueError('Number of vertices MUST be at least 4.')
    if height <= 0 or width <= 0:
        raise ValueError('Height and width MUST be positive.')
    if inner_height is None:
        inner_height = 0.1 * height
    elif inner_height >= height:
        raise ValueError('Inner height MUST be less than height.')

    points = deque([Point(0, height).round(round)])
    half_n = n // 2
    center_point = half_n * 2 == n
    width /= 2
    for i in range(half_n):
        if i + 1 == half_n and center_point:
            points.append(Point(0, inner_height).round(round))
            continue

        x = i * width / half_n
        x_exp = i / half_n * log(100)
        points.append(Point(-width + x, inner_height * (1 - exp(-x_exp))).round(round))
        points.appendleft(Point(width - x, inner_height * (1 - exp(-x_exp))).round(round))

    return points


@polygon
def pathological_01(n: int, height: float, width: float, inner_height: float = None, round: int = 4
                    ) -> Union[Polygon, TriangulatedPolygon]:
    """A concave triangle with one point at the top and many points on the bottom."""
    if n < 5:
        raise ValueError('Number of vertices MUST be at least 5.')
    if height <= 0 or width <= 0:
        raise ValueError('Height and width MUST be positive.')
    if inner_height is None:
        inner_height = 0.9 * height
    elif inner_height >= height:
        raise ValueError('Inner height MUST be less than height.')

    stretch = - inner_height / (width * width)

    points = deque()
    points_per_side = (n - 4) // 2
    if n % 2 == 1:
        points.append(Point(0, inner_height).round(round))

    for i in range(points_per_side):
        x = (i + 1) * width / (points_per_side + 1)
        y = stretch * x * x + inner_height

        points.append(Point(x, y).round(round))
        points.appendleft(Point(-x, y).round(round))

    points.append(Point(width, 0).round(round))
    points.appendleft(Point(-width, 0).round(round))

    points.append(Point(width, height).round(round))
    points.appendleft(Point(-width, height).round(round))

    return points


@polygon
def pathological_02(n: int, height: float, width: float, ellipse_percentage: float = None, round: int = 4
                    ) -> Union[Polygon, TriangulatedPolygon]:
    """A concave triangle like pathological_01 but the concave part is 1/4 circle from top left to bottom right."""
    if n < 5:
        raise ValueError('Number of vertices MUST be at least 5.')
    if height <= 0 or width <= 0:
        raise ValueError('Height and width MUST be positive.')
    if ellipse_percentage is None:
        ellipse_percentage = 0.99
    elif ellipse_percentage >= 1 or ellipse_percentage <= 0:
        raise ValueError('Ellipse size MUST be in the range (0, 1) (exclusive).')

    points = [Point(0, height * ellipse_percentage), Point(0, height), Point(width, height), Point(width, 0),
              Point(ellipse_percentage * width, 0)]

    points_on_circle = n - 3
    angle_per_point = pi / 2 / (points_on_circle - 1)

    for i in range(1, points_on_circle - 1):
        points.append(Point(cos(i * angle_per_point) * width * ellipse_percentage,
                            sin(i * angle_per_point) * height * ellipse_percentage))

    return reversed(points)


@polygon
def pathological_03(n: int, size: float, percentage: float = None, round: int = 4
                    ) -> Union[Polygon, TriangulatedPolygon]:
    """A concave triangle with one point at the top and many points on the bottom."""
    if n < 5:
        raise ValueError('Number of vertices MUST be at least 5.')
    if size <= 0:
        raise ValueError('Size MUST be positive.')
    if percentage is None:
        percentage = 0.95
    elif percentage >= 1 or percentage <= 0:
        raise ValueError('Percentage MUST be in the range (0, 1) (exclusive).')

    points = [Point(0, size * percentage), Point(-size * (1 - percentage) / 2, size * percentage), Point(size, size),
              Point(size * percentage, 0)]

    points_on_circle = n // 4
    angle_per_point = pi / 2 / points_on_circle

    for i in range(1, points_on_circle):
        points.append(Point(cos(i * angle_per_point) * size * percentage,
                            sin(i * angle_per_point) * size * percentage))
        points.append(Point(size * percentage, -i ** 2 / points_on_circle ** 2 * size * percentage))
        points.append(Point(size + i / points_on_circle * size * percentage, size))
        points.append(Point(size * percentage, -(i + .5) ** 2 / points_on_circle ** 2 * size * percentage))

    return reversed(points)


@polygon
def convex_sleeve_polygon(n: int, height: float, width: float = None, distance: float = None, round: int = 4
                          ) -> Union[Polygon, TriangulatedPolygon]:
    """Creae a sleeve-like polygon with the upper and lower boundary bending outwards, creating a convex polygon."""
    if n < 3:
        raise ValueError('Number of vertices MUST be at least 3.')
    if (width is None and distance is None) or (width is not None and distance is not None):
        raise ValueError('Either width or distance MUST be given.')

    if width is None:
        width = distance * (n - 1)
    elif distance is None:
        distance = width / (n - 1)
    if height <= 0 or width <= 0:
        raise ValueError('Height and width/distance MUST be positive.')

    number_of_low_points = (n + 1) // 2
    number_of_high_points = n - number_of_low_points

    rightmost_low_x = number_of_low_points * 2 * distance

    def f(x: float):
        return (x - rightmost_low_x / 2) ** 2 * 4 / (rightmost_low_x ** 2)

    points = []
    for i in range(number_of_low_points):
        x = 2 * distance * i
        points.append(Point(x, f(x)).round(round))

    for i in range(number_of_high_points):
        x = distance * (2 * number_of_high_points - 1 - 2 * i)
        points.append(Point(x, height - f(x)).round(round))

    return points


@polygon
def polygon_from_database(id: int) -> Union[Polygon, TriangulatedPolygon]:
    """Load a polygon from the PostgreSQL database."""
    m_points = model.PolygonPoint.select(model.PolygonPoint, model.Point).join(model.Point).where(
        model.PolygonPoint.polygon == id, model.PolygonPoint.is_vertex).order_by(model.PolygonPoint.index)
    for m_point in m_points:
        yield Point(float(m_point.point.x), float(m_point.point.y))


@polygon
def polygon_001() -> Union[Polygon, TriangulatedPolygon]:
    """Create a very specific polygon."""
    return (Point(x, y) for x, y in
            [(0.1, 0), (2.9, 0.2), (3, 3), (4.1, 1), (4, 3.9), (5.1, 2), (5, 4), (7, 0.1), (4.9, 5.9), (0, 6)])
