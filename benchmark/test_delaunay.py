#!/usr/bin/env python3.5
"""Run tests on Delaunay against Lee-Preparata."""
import argparse
import os.path
import signal
from math import ceil
from typing import List

import traceback
from matplotlib import pyplot

from benchmark.executer import create_random_polygons
from defaults import dpi, font_size, size, ticks
from draw import draw_polygon
from geometry import LineSegment
from geometry import Point, Polygon
from geometry import PolygonPoint
from geometry.exceptions import NotInGeneralPositionException, ThreePointsAreCollinearException
from gsp import lee_preparata_shortest_path, delaunay_shortest_path


def save_polygon(basename: str, polygon: Polygon, delaunay_path: List[Point] = None,
                 lee_preparata_path: List[Point] = None, s: int = None, t: int = None):
    """Plot a polygon (with paths) and save it to a file."""
    if delaunay_path is None and lee_preparata_path is None and polygon in save_polygon.polygons:
        return

    if delaunay_path is None and lee_preparata_path is None:
        with open(basename + '.polygon', 'w') as f:
            for p in polygon.points:
                print('{0:f} {1:f}'.format(p.x, p.y), file=f)

    if polygon not in save_polygon.polygons and not (delaunay_path is None and lee_preparata_path is None):
        save_polygon(basename, polygon)

    if polygon not in save_polygon.polygons:
        save_polygon.polygons.append(polygon)

    pyplot.ioff()
    fig, ax = pyplot.subplots()
    draw_polygon(ax, polygon)
    pyplot.draw()

    if delaunay_path is not None:
        ax.plot(list([p.x for p in delaunay_path]), list([p.y for p in delaunay_path]),
                color='red', linestyle='--', marker='*', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('delaunay', xy=delaunay_path[0].tuple(),
                    xytext=(
                        delaunay_path[0].x + size / ticks / 20,
                        delaunay_path[0].y + size / ticks / 20),
                    fontsize=font_size, color='red', alpha=.8)

    if lee_preparata_path is not None:
        ax.plot(list([p.x for p in lee_preparata_path]), list([p.y for p in lee_preparata_path]),
                color='orange', linestyle=':', marker='s', markersize=2, zorder=99, linewidth=.75, alpha=.5)
        ax.annotate('lee_preparata', xy=lee_preparata_path[0].tuple(),
                    xytext=(
                        lee_preparata_path[0].x + size / ticks / 20,
                        lee_preparata_path[0].y - size / ticks / 20),
                    fontsize=font_size, color='orange', alpha=.8)

    image_pattern = '{basename}.png'
    image_path_pattern = '{basename}:{s:03d}->{t:03d}.png'

    if lee_preparata_path is None and delaunay_path is None:
        fig.savefig(image_pattern.format(basename=basename),
                    dpi=dpi, bbox_inches='tight', pad_inches=.01)
    else:
        fig.savefig(image_path_pattern.format(basename=basename, s=s, t=t),
                    dpi=dpi, bbox_inches='tight', pad_inches=.01)
    pyplot.close()

save_polygon.polygons = []


def timeout(_, __):
    """Raise timeout error."""
    raise TimeoutError()


def test_algorithms(path, polygon, s, t, pictures):
    """Run all algorithms on the given polygon and check that the results are equal."""
    timeout = 60
    name = str(abs(hash(repr(polygon))))
    file_name = os.path.join(path, name)

    try:
        signal.alarm(timeout)
        delaunay_path = list(delaunay_shortest_path(polygon, Point(*s.tuple()), Point(*t.tuple())))
    except TimeoutError:
        print('\nDelaunay calculation took longer than {0}s!'.format(timeout))
        return
    except NotInGeneralPositionException:
        print('\nPolygon not in general position!')
        return
    except BaseException:
        save_polygon(file_name, polygon)
        with open(file_name + '.exception', 'w') as f:
            print('Delaunay-Exception', file=f)
            print('{0} -> {1}\n'.format(s, t), file=f)
            traceback.print_exc(file=f)
        traceback.print_exc()
        return
    finally:
        signal.alarm(0)

    try:
        signal.alarm(timeout)
        lee_preparata_path = list(lee_preparata_shortest_path(polygon, Point(*s.tuple()), Point(*t.tuple())))
    except TimeoutError:
        print('Lee-Preparata calculation took to longer than {0}s!'.format(timeout))
        return
    except BaseException:
        save_polygon(file_name, polygon)
        with open(file_name + '.exception', 'w') as f:
            print('Lee-Preparata-Exception', file=f)
            print('{0} -> {1}\n'.format(s, t), file=f)
            traceback.print_exc(file=f)
        traceback.print_exc()
        return
    finally:
        signal.alarm(0)

    error = False

    if delaunay_path != lee_preparata_path:
        if pictures:
            save_polygon(file_name, polygon, delaunay_path, lee_preparata_path, s.index, t.index)
        print('\nFailed: {path}, {s} -> {t}'.format(path=name, s=s.index, t=t.index))
        error = True

    if not error:
        for path_ix in range(len(delaunay_path) - 1):
            for edge_ix in range(len(polygon)):
                if polygon.edge(edge_ix).properly_intersects(
                        LineSegment(delaunay_path[path_ix], delaunay_path[path_ix + 1])):
                    if pictures:
                        save_polygon(file_name, polygon, delaunay_path, lee_preparata_path, s, t)
                    print('\nFailed: {path}, {s} -> {t}'.format(path=name, s=s.index, t=t.index))
                    error = True
                    break
            if error:
                break

    print('.', end='', flush=True)


def main(n, pictures, folder):
    """Run infinitely many tests."""
    signal.signal(signal.SIGALRM, timeout)

    polygons = 0

    while True:
        try:
            for polygon in create_random_polygons(n, 10):

                all_x = set()
                for p in polygon.points:
                    all_x.add(p.x)
                if len(all_x) != len(polygon):
                    continue

                print('\nnew polygon: ', end='', flush=True)

                # Get set of unique points
                tuples = set()
                points = []
                try:
                    for index in range(len(polygon)):
                        point = polygon.point_inside_at(index)

                        if point.tuple() not in tuples:
                            tuples.add(point.tuple())
                            points.append(PolygonPoint(point, index=index))
                except ThreePointsAreCollinearException:
                    print('collinear', end='', flush=True)
                    continue

                # Loop through all pairs
                for s in points:
                    for t in points:
                        if s == t:
                            continue

                        test_algorithms(folder, polygon, s, t, pictures)

                polygons += 1
        except KeyboardInterrupt:
            break
        except IndexError:
            pass

    print('\n\nTested {0} complete polygons with size {1} each.'.format(polygons, n))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test delaunay against Lee-Preparata.')
    parser.add_argument('-n', '--no-pictures', action='store_false', help='do NOT generate picture', dest='pictures')
    parser.add_argument('size', type=int, help='number of vertices')
    parser.add_argument('-f', '--folder', type=str,
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fails'))

    args = parser.parse_args()

    print(args)

    main(args.size, args.pictures, args.folder)
