"""Tests the point_sees_edge method."""

import os
from glob import glob
from os.path import splitext, basename
from typing import Tuple, List

from matplotlib import pyplot

from defaults import size, font_size, ticks, dpi
from draw import draw_polygon
from geometry import Polygon, LineSegment, Point
from gsp import delaunay, trapezoid


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
                point, rest = line.strip().split('<')
                edge, visible = rest.split(':')

                point = int(point)
                edge = int(edge)
                visible = int(visible) == 1

                point_data.append((point, edge, visible))

    if not polygon_data:
        raise ValueError('No data read from file.')

    polygon_data = list(map(lambda tup: Point(float(tup[0]), float(tup[1])), polygon_data))

    return Polygon(polygon_data), point_data


def pytest_generate_tests(metafunc):
    """Generate test cases."""
    idlist = []
    argnames = ['polygon', 'point', 'edge', 'visible']
    argvalues = []

    for file in metafunc.cls.files:
        if basename(file).startswith('_'):
            continue

        polygon, data = load_test_polygon(file)
        for point, edge, visible in data:
            idlist.append('{0};{1}<{2}:{3}'.format(os.path.basename(file), point, edge, visible))
            argvalues.append([polygon, polygon.point(point), polygon.edge(edge), visible])

    metafunc.parametrize(argnames, argvalues, ids=idlist, scope='class')


class TestPointSeesEdge(object):
    """Test class to generate test cases from multiple files."""

    files = glob(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data/*.pointtest')

    def test_method(self, polygon, point, edge, visible):
        """Test visibility from point to edge."""
        assert isinstance(polygon, Polygon)

        sees_edge = polygon.point_sees_edge2(point, edge)

        if not visible:
            assert not sees_edge
        else:
            assert sees_edge
