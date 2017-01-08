"""Tests the gsp algorithms against each other."""

import os
import signal
from glob import glob
from math import ceil
from os.path import basename, splitext
from typing import List, Tuple

from matplotlib import pyplot

from defaults import dpi, font_size, size, ticks
from draw import draw_polygon
from geometry import LineSegment, Point, Polygon
from gsp import delaunay_shortest_path, makestep_shortest_path, trapezoid_shortest_path


def save_polygon(basename: str, polygon: Polygon, trapezoid_path: List[Point] = None,
                 delaunay_path: List[Point] = None, makestep_path: List[Point] = None,
                 s: int = None, t: int = None):
    """Plot a polygon (with paths) and save it to a file."""
    if trapezoid_path is None and delaunay_path is None and polygon in save_polygon.polygons:
        return

    if polygon not in save_polygon.polygons and (trapezoid_path is not None or delaunay_path is not None):
        save_polygon(basename, polygon)

    if polygon not in save_polygon.polygons:
        save_polygon.polygons.append(polygon)

    pyplot.ioff()
    fig, ax = pyplot.subplots()
    draw_polygon(ax, polygon)
    pyplot.draw()

    if trapezoid_path is not None:
        ax.plot(list([p.x for p in trapezoid_path]), list([p.y for p in trapezoid_path]),
                color='magenta', linestyle='--', marker='*', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('trapezoid', xy=trapezoid_path[0].tuple(),
                    xytext=(
                        trapezoid_path[0].x + size / ticks / 20,
                        trapezoid_path[0].y + size / ticks / 20),
                    fontsize=font_size, color='magenta', alpha=.8)

    if delaunay_path is not None:
        ax.plot(list([p.x for p in delaunay_path]), list([p.y for p in delaunay_path]),
                color='green', linestyle=':', marker='s', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('delaunay', xy=delaunay_path[0].tuple(),
                    xytext=(
                        delaunay_path[0].x + size / ticks / 20,
                        delaunay_path[0].y - size / ticks / 20),
                    fontsize=font_size, color='green', alpha=.8)

    if makestep_path is not None:
        ax.plot(list([p.x for p in makestep_path]), list([p.y for p in makestep_path]),
                color='red', linestyle='-.', marker='^', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('makestep', xy=makestep_path[0].tuple(),
                    xytext=(
                        makestep_path[0].x + size / ticks / 20,
                        makestep_path[0].y - 3 * size / ticks / 20),
                    fontsize=font_size, color='red', alpha=.8)

    image_pattern = '{basename}.png'
    image_path_pattern = '{basename}:{s:03d}->{t:03d}.png'

    if delaunay_path is None and trapezoid_path is None and makestep_path is None:
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

    try:
        if metafunc.config.getoption('--single-tests'):
            with open(metafunc.cls.single_test_file, 'r') as f:
                for line in f:
                    filename, s_t = line.strip().split(';')
                    s, t = s_t.split('->')
                    file_path = os.path.join(metafunc.cls.base_path, filename)
                    polygon, _ = load_test_polygon(file_path)
                    idlist.append(line.strip())
                    argvalues.append([splitext(file_path)[0], polygon, int(s), int(t)])

        else:
            for file in metafunc.cls.img_files:
                os.remove(file)

            ignored = []
            with open(metafunc.cls.ignore_file, 'r') as f:
                for line in f:
                    ignored.append(line.strip())

            for file in metafunc.cls.files:
                if basename(file) in ignored:
                    continue

                polygon, points = load_test_polygon(file)
                for s, t in points:
                    idlist.append('{0};{1}->{2}'.format(os.path.basename(file), s, t))
                    path = splitext(file)[0]
                    argvalues.append([path, polygon, s, t])
    except BaseException:
        pass

    metafunc.parametrize(argnames, argvalues, ids=idlist, scope='class')


class TestGSPAlgorithmsViaCrossTest(object):
    """Test various gsp algorithms via cross test (i.e. run all, check that output is always the same)."""

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data'
    ignore_file = base_path + '/polytest'
    single_test_file = base_path + '/single-tests'
    files = glob(base_path + '/*.polytest')
    img_files = glob(base_path + '/*.png')

    def test_algorithms(self, path, polygon, s, t, pictures, ignore_delaunay):
        """Run all algorithms on the given polygon and check that the results are equal."""
        assert isinstance(polygon, Polygon)

        signal.signal(signal.SIGALRM, timeout)

        s_point = polygon.point_inside_at(s)
        t_point = polygon.point_inside_at(t)

        cubed_timeout = ceil(0.001 * polygon.len ** 3)
        squared_timeout = ceil(0.001 * polygon.len ** 2)

        delaunay_path = None

        if not ignore_delaunay:
            signal.alarm(cubed_timeout)
            try:
                delaunay_path = list(delaunay_shortest_path(polygon, s_point, t_point))
                signal.alarm(0)
            except TimeoutError:
                raise TimeoutError('Delaunay calculation took longer than {0}s!'.format(cubed_timeout))

        signal.alarm(squared_timeout)
        try:
            trapezoid_path = list(trapezoid_shortest_path(polygon, s_point, t_point))
            signal.alarm(0)
        except TimeoutError:
            raise TimeoutError('Trapezoid calculation took longer than {0}s!'.format(squared_timeout))

        signal.alarm(squared_timeout)
        try:
            makestep_path = list(makestep_shortest_path(polygon, s_point, t_point))
            signal.alarm(0)
        except TimeoutError:
            raise TimeoutError('Makestep calculation took to longer than {0}s!'.format(squared_timeout))

        if (not delaunay_path == trapezoid_path == makestep_path and delaunay_path is not None) or (
                not trapezoid_path == makestep_path):
            if pictures:
                save_polygon(path, polygon, trapezoid_path, delaunay_path, makestep_path, s, t)

            assert delaunay_path == trapezoid_path
            assert delaunay_path == makestep_path
            assert makestep_path == trapezoid_path

        for path_ix in range(len(trapezoid_path) - 1):
            for edge_ix in range(len(polygon)):
                if polygon.edge(edge_ix).properly_intersects(
                        LineSegment(trapezoid_path[path_ix], trapezoid_path[path_ix + 1])):
                    if pictures:
                        save_polygon(path, polygon, trapezoid_path, delaunay_path, makestep_path, s, t)

                    assert not polygon.edge(edge_ix).properly_intersects(
                        LineSegment(trapezoid_path[path_ix], trapezoid_path[path_ix + 1]))
