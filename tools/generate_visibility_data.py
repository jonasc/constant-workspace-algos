#!/usr/bin/env python3.5
"""
Shows polygons with the ability to decide whether a point sees an edge.

The generated data can then be used for automated tests.
"""

import os.path
import sys

import matplotlib.pyplot as plt
from matplotlib.backend_bases import KeyEvent, MouseEvent

from draw import draw_polygon
from geometry import Point, PolygonPoint
from geometry.polygon_loader import load_polygon


def next_edge():
    """Select next edge in polygon."""
    for key, obj in next_edge.obj.items():
        if obj is not None:
            try:
                obj.remove()
                next_edge.obj[key] = None
            except BaseException:
                pass

    if next_edge.edge is None or next_edge.edge >= len(polygon):
        return

    edge = polygon.edge(next_edge.edge)

    next_edge.obj['edge'] = plt.Polygon([edge.a.tuple(), edge.b.tuple()], color='green', linewidth=2)
    plt.gca().add_patch(next_edge.obj['edge'])

    next_edge.obj['view'] = plt.Polygon([edge.a.tuple(), next_edge.point.tuple(), edge.b.tuple()], color='gray',
                                        linewidth=1, alpha=0.1)
    plt.gca().add_patch(next_edge.obj['view'])

    if next_edge.point.index in on_key_press.data and next_edge.edge in on_key_press.data[next_edge.point.index]:
        if on_key_press.data[next_edge.point.index][next_edge.edge]:
            next_edge.obj['view'].set_color('green')
        else:
            next_edge.obj['view'].set_color('red')

    next_edge.obj['point'] = plt.Circle(next_edge.point.tuple(), .05, color='blue')
    plt.gca().add_patch(next_edge.obj['point'])

    plt.draw()


next_edge.point = None
next_edge.edge = None
next_edge.obj = dict(edge=None, point=None, view=None)


def on_key_press(event: KeyEvent):
    """React to key presses."""
    if event.key == 'q':
        with open(on_key_press.file, 'w') as f:
            for point in polygon.points:
                assert isinstance(point, Point)
                print('{0:.4f} {1:.4f}'.format(point.x, point.y), file=f)

            print('%' * 20, file=f)

            for point, edges in sorted(on_key_press.data.items()):
                for edge, visible in sorted(edges.items()):
                    print('{0}<{1}:{2}'.format(point, edge, visible * 1), file=f)

        sys.exit()

    if event.key not in ('enter', 'delete', ' ', 'b'):
        return

    if next_edge.edge is None:
        return

    if event.key == ' ':
        next_edge.edge += 1
    elif event.key == 'b':
        next_edge.edge -= 1
    elif event.key in ('enter', 'delete'):
        assert isinstance(next_edge.point, PolygonPoint)

        if next_edge.point.index not in on_key_press.data:
            on_key_press.data[next_edge.point.index] = dict()

        on_key_press.data[next_edge.point.index][next_edge.edge] = event.key == 'enter'

        if on_key_press.data[next_edge.point.index][next_edge.edge]:
            next_edge.obj['view'].set_color('green')
        else:
            next_edge.obj['view'].set_color('red')
        plt.draw()

        next_edge.edge += 1

    next_edge.edge %= len(polygon)
    next_edge()


on_key_press.data = dict()


def on_mouse_press(event: MouseEvent):
    """Select the nearest vertex to the mouse for visiblity checks."""
    if event.button == 3:
        clicked_point = Point(event.xdata, event.ydata)
        nearest = None
        nearest_dist = None
        dist = None
        for polygon_point in polygon.points:
            if nearest is None:
                nearest = polygon_point
                nearest_dist = clicked_point.squared_distance_to(nearest)
            else:
                dist = clicked_point.squared_distance_to(polygon_point)
                if dist < nearest_dist:
                    nearest = polygon_point
                    nearest_dist = dist

        assert nearest is not None

        next_edge.point = nearest
        next_edge.edge = 0
        next_edge()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Give exactly one parameter!')
        sys.exit(2)

    polygon = load_polygon(sys.argv[1])

    on_key_press.file = os.path.splitext(sys.argv[1])[0] + '.pointtest'

    if os.path.exists(on_key_press.file):
        with open(on_key_press.file, 'r') as f:
            points = True
            for l in f:
                if l.startswith('%'):
                    points = False
                    continue

                if points:
                    continue

                point, rest = l.strip().split('<')
                edge, visible = rest.split(':')

                point = int(point)
                edge = int(edge)
                visible = int(visible) == 1

                if point not in on_key_press.data:
                    on_key_press.data[point] = dict()

                on_key_press.data[point][edge] = visible

    fig, ax = plt.subplots()
    draw_polygon(ax, polygon)
    fig.canvas.mpl_connect('button_release_event', on_mouse_press)
    fig.canvas.mpl_connect('key_release_event', on_key_press)
    plt.show()
