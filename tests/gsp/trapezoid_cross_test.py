"""Tests the trapezoid algorithm against Lee-Preparata."""

import os
import signal
from math import ceil
from os.path import basename, splitext
from typing import List, Tuple

from matplotlib import pyplot

from benchmark.executer import get_polygons
from defaults import dpi, font_size, size, ticks
from draw import draw_polygon
from geometry import LineSegment, Point, Polygon
from gsp import lee_preparata_shortest_path, trapezoid_shortest_path


def save_polygon(basename: str, polygon: Polygon, trapezoid_path: List[Point] = None,
                 lee_preparata_path: List[Point] = None, s: int = None, t: int = None):
    """Plot a polygon (with paths) and save it to a file."""
    if trapezoid_path is None and lee_preparata_path is None and polygon in save_polygon.polygons:
        return

    if polygon not in save_polygon.polygons and not (trapezoid_path is None and lee_preparata_path is None):
        save_polygon(basename, polygon)

    if polygon not in save_polygon.polygons:
        save_polygon.polygons.append(polygon)

    pyplot.ioff()
    fig, ax = pyplot.subplots()
    draw_polygon(ax, polygon)
    pyplot.draw()

    if trapezoid_path is not None:
        ax.plot(list([p.x for p in trapezoid_path]), list([p.y for p in trapezoid_path]),
                color='blue', linestyle='--', marker='*', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('trapezoid', xy=trapezoid_path[0].tuple(),
                    xytext=(
                        trapezoid_path[0].x + size / ticks / 20,
                        trapezoid_path[0].y + size / ticks / 20),
                    fontsize=font_size, color='blue', alpha=.8)

    if lee_preparata_path is not None:
        ax.plot(list([p.x for p in lee_preparata_path]), list([p.y for p in lee_preparata_path]),
                color='orange', linestyle=':', marker='s', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('delaunay', xy=lee_preparata_path[0].tuple(),
                    xytext=(
                        lee_preparata_path[0].x + size / ticks / 20,
                        lee_preparata_path[0].y - size / ticks / 20),
                    fontsize=font_size, color='orange', alpha=.8)

    image_pattern = '{basename}.png'
    image_path_pattern = '{basename}:{s:03d}->{t:03d}.png'

    if lee_preparata_path is None and trapezoid_path is None:
        fig.savefig(image_pattern.format(basename=basename),
                    dpi=dpi, bbox_inches='tight', pad_inches=.01)
    else:
        fig.savefig(image_path_pattern.format(basename=basename, s=s, t=t),
                    dpi=dpi, bbox_inches='tight', pad_inches=.01)
    pyplot.close()


save_polygon.polygons = []


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
    """Raise timeout error."""
    raise TimeoutError()


def pytest_generate_tests(metafunc):
    """Generate test data from input file(s)."""
    idlist = []
    argnames = ['path', 'polygon', 's', 't']
    argvalues = []
    path_format = '{0:03d}'

    try:
        index = 0
        for polygon in get_polygons('random', metafunc.config.getoption('--2nd-level'), metafunc.config.getoption('--1st-level')):
            while True:
                path = path_format.format(index)
                try:
                    with open(os.path.join(metafunc.cls.base_path, path + '.polygon'), 'x') as f:
                        for p in polygon.points:
                            print('{0:f} {1:f}'.format(p.x, p.y), file=f)
                    index += 1
                    break
                except OSError:
                    index += 1

            points = set()
            for index in range(len(polygon)):
                point = polygon.point_inside_at(index)
                points.add(point.tuple())

            no_points = 0
            for s in map(lambda t: Point(t[0], t[1]), points):
                for t in map(lambda t: Point(t[0], t[1]), points):
                    if s == t:
                        continue

                    idlist.append('{0};{1}->{2}'.format(path, s, t))
                    argvalues.append([path, polygon, s, t])

    except BaseException as e:
        pass

    metafunc.parametrize(argnames, argvalues, ids=idlist, scope='class')


class TestGSPAlgorithmsViaCrossTest(object):
    """Test various gsp algorithms via cross test (i.e. run all, check that output is always the same)."""

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/tr-lp-data'

    def test_algorithms(self, path, polygon, s, t, pictures):
        """Run all algorithms on the given polygon and check that the results are equal."""
        assert isinstance(polygon, Polygon)

        signal.signal(signal.SIGALRM, timeout)

        squared_timeout = ceil(0.001 * polygon.len ** 2)

        try:
            signal.alarm(squared_timeout)
            trapezoid_path = list(trapezoid_shortest_path(polygon, s, t))
            signal.alarm(0)
        except TimeoutError:
            raise TimeoutError('Trapezoid calculation took longer than {0}s!'.format(squared_timeout))

        try:
            signal.alarm(squared_timeout)
            lee_preparata_path = list(lee_preparata_shortest_path(polygon, s, t))
            signal.alarm(0)
        except TimeoutError:
            raise TimeoutError('Lee-Preparata calculation took to longer than {0}s!'.format(squared_timeout))

        if trapezoid_path != lee_preparata_path:
            if pictures:
                save_polygon(path, polygon, trapezoid_path, lee_preparata_path, s, t)

            assert trapezoid_path == lee_preparata_path

        for path_ix in range(len(trapezoid_path) - 1):
            for edge_ix in range(len(polygon)):
                if polygon.edge(edge_ix).properly_intersects(
                        LineSegment(trapezoid_path[path_ix], trapezoid_path[path_ix + 1])):
                    if pictures:
                        save_polygon(path, polygon, trapezoid_path, lee_preparata_path, s, t)

                    assert not polygon.edge(edge_ix).properly_intersects(
                        LineSegment(trapezoid_path[path_ix], trapezoid_path[path_ix + 1]))
