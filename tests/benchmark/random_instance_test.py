"""Benchmark the gsp algorithms."""

import os
import signal
from glob import glob
from os.path import splitext, basename
from typing import Tuple, List

from geometry import Polygon, LineSegment, Point, PolygonPoint
from gsp import delaunay_shortest_path, trapezoid_shortest_path, makestep_shortest_path


def load_test_polygon(filename: str) -> Tuple[Polygon, List[Tuple[int, int]]]:
    """Load a polygon and start/end point data from a file."""
    polygon_data = []
    point_data = []
    with open(filename, 'r') as f:
        polygon = True
        for line in f:
            if line.startswith('%'):
                polygon = False
                continue

            if polygon:
                polygon_data.append(line.strip().split(' '))
            else:
                point_data.append(line.strip().split('->'))

    if not polygon_data:
        raise ValueError('No data read from file.')

    polygon_data = list(map(lambda tup: Point(float(tup[0]), float(tup[1])), polygon_data))
    point_data = list(map(lambda tup: (int(tup[0]), int(tup[1])), point_data))

    return Polygon(polygon_data), point_data


def timeout(_, __):
    """Raise a rimeout error."""
    raise TimeoutError()


def pytest_generate_tests(metafunc):
    """Generate tests from data read from a given file."""
    idlist = []
    argnames = ['polygon', 's', 't']
    argvalues = []

    polygon_file = metafunc.config.getoption('--benchmark-polygon')

    if polygon_file is None:
        metafunc.parametrize(argnames, argvalues, ids=idlist)
        return

    polygon, _ = load_test_polygon(polygon_file)

    points = []
    for p_ix in range(len(polygon)):
        point = polygon.point_inside_at(p_ix)
        found = False
        for other_point in points:
            if Point.__eq__(point, other_point):
                found = True
        if not found:
            points.append(PolygonPoint(point, index=p_ix))

    for s in points:
        for t in points:
            if s == t:
                continue
            idlist.append('{0}->{1}'.format(s.index, t.index))
            argvalues.append([polygon, s, t])

    metafunc.parametrize(argnames, argvalues, ids=idlist)


def compute_full_path(func, polygon, s, t):
    """Run the shortest path computation func on the given input data with timeout limit.."""
    signal.alarm(5)
    try:
        r = list(func(polygon, s, t))
    except TimeoutError:
        raise TimeoutError('Calculation took to much time!')
    signal.alarm(0)
    return r


signal.signal(signal.SIGALRM, timeout)


class TestBenchmarkGSPAlgorithms(object):
    """Test class to run all known algorithms."""

    def test_delaunay(self, polygon, s, t, pictures, benchmark):
        """Run the delaunay algorithm."""
        benchmark(compute_full_path, delaunay_shortest_path, polygon, s, t)

    def test_trapezoid(self, polygon, s, t, pictures, benchmark):
        """Run the trapezoid algorithm."""
        benchmark(compute_full_path, trapezoid_shortest_path, polygon, s, t)

    def test_makestep(self, polygon, s, t, pictures, benchmark):
        """Run the makestep algorithm."""
        benchmark(compute_full_path, makestep_shortest_path, polygon, s, t)
