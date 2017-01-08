"""Test configuration."""

import pytest
from hypothesis.strategies import builds, integers, floats, lists

from geometry import Point, Polygon, TriangulatedPolygon


########################################################################################################################
# PY.TEST COMMAND LINE OPTIONS
########################################################################################################################
def pytest_addoption(parser):
    """Add some options to the cli argument parser."""
    parser.addoption('--limit', default=10000, type=int, help='limits for coordinates')
    parser.addoption('--epsilon', default=1e-6, type=float, help='smallest point comparison error')
    parser.addoption('--1st-level', default=100, type=int, help='number of first-level objects to test')
    parser.addoption('--2nd-level', default=100, type=int, help='number of second-level objects to test')
    parser.addoption('--pictures', default=False, action='store_true', help='generate picture')
    parser.addoption('--single-tests', action='store_true', help='run single tests')
    parser.addoption('--benchmark-polygon', default=None, type=str, help='which polygon to benchmark')
    parser.addoption('--no-delaunay', action='store_true', help='ignore delaunay during cross test')


########################################################################################################################
# PY.TEST FIXTURES
########################################################################################################################
@pytest.fixture
def limit(request):
    """Return fixture value from cli."""
    return request.config.getoption('--limit')


@pytest.fixture
def epsilon(request):
    """Return fixture value from cli."""
    return request.config.getoption('--epsilon')


@pytest.fixture
def first_level(request):
    """Return fixture value from cli."""
    return request.config.getoption('--1st-level')


@pytest.fixture
def second_level(request):
    """Return fixture value from cli."""
    return request.config.getoption('--2nd-level')


@pytest.fixture
def pictures(request):
    """Return fixture value from cli."""
    return request.config.getoption('--pictures')


@pytest.fixture
def ignore_delaunay(request):
    """Return fixture value from cli."""
    return request.config.getoption('--no-delaunay')


########################################################################################################################
# HYPOTHESIS STRATEGIES
########################################################################################################################
points = builds(
    Point,
    integers() |
    floats(min_value=-1e50, max_value=+1e50, allow_nan=False, allow_infinity=False).filter(
        lambda x: abs(x) > 1e-30 or x == 0),
    integers() |
    floats(min_value=-1e50, max_value=+1e50, allow_nan=False, allow_infinity=False).filter(
        lambda x: abs(x) > 1e-30 or x == 0),
)


def is_valid_polygon(polygon: Polygon) -> bool:
    """Check that no pair of edges in the given polygon properly intersects. Additionally check for general position."""
    for i, edge_i in enumerate(polygon.edges()):
        for j, edge_j in enumerate(polygon.edges()):
            if i != j and edge_i.properly_intersects(edge_j):
                return False
            if j not in ((i + 1) % len(polygon), (i - 1) % len(polygon)) and edge_i.intersects(edge_j):
                return False

    # Make sure there are no three points on a line
    for p in polygon.points:
        for q in polygon.points:
            if p == q:
                continue
            for r in polygon.points:
                if p == r or q == r:
                    continue
                if Point.turn(p, q, r) == Point.NO_TURN:
                    return False

    return True


polygons = builds(
    Polygon,
    lists(points, min_size=3, max_size=20, unique_by=lambda p: p.tuple())
).filter(is_valid_polygon)

triangulated_polygons = builds(TriangulatedPolygon, polygons)
