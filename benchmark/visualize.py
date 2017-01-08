#!/usr/bin/env python3.5
"""Visualize various objects like polygons, run paths etc."""
import argparse
import sys

from benchmark.plot import plot_colors


def plot_polygon(id, pattern):
    """Plot a polygon with a given database id into a file with the given pattern."""
    m_polygon = model.Polygon.get(model.Polygon.id == id)
    pyplot.figure(figsize=(20, 20))
    pyplot.gcf().clear()
    draw_polygon(pyplot.gca(), m_polygon.as_geometry())
    pyplot.title('polygon {polygon_id}'.format(polygon_id=id))
    pyplot.draw()
    pyplot.savefig(pattern.format(id=id), dpi='figure', bbox_inches='tight', pad_inches=0.1)


def plot_run(id, pattern):
    """Plot a run with a given database id into a file with the given pattern."""
    m_run = model.Run.get(model.Run.id == id)
    pyplot.figure(figsize=(20, 20))
    pyplot.gcf().clear()
    draw_polygon(pyplot.gca(), m_run.polygon.as_geometry())

    m_points = (m_run.run_path_points
                .select(model.RunPathPoint, model.Algorithm, model.Point)
                .join(model.PolygonPoint).join(model.Point)
                .switch(model.RunPathPoint).join(model.Algorithm)
                )

    points = []
    algorithm = None

    def plot(pts):
        pyplot.plot([p[0] for p in pts], [p[1] for p in pts],
                    color=plot_colors[algorithm], marker='x', markersize=3, label=algorithm)

    for m_point in m_points:
        if algorithm is None or algorithm != m_point.algorithm.name:
            if points:
                plot(points)

            points = []
            algorithm = m_point.algorithm.name

        points.append((float(m_point.polygon_point.point.x), float(m_point.polygon_point.point.y)))

    if points:
        plot(points)

    pyplot.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=4, mode='expand', borderaxespad=0.)
    pyplot.title('run {run_id}; polygon {polygon_id}'.format(run_id=id, polygon_id=m_run.polygon_id))

    pyplot.draw()
    pyplot.savefig(pattern.format(id=id), dpi='figure', bbox_inches='tight', pad_inches=0.1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize various objects.')

    parser.add_argument('-p', '--polygon', action='append', default=[], help='plot the polygon with this id')
    parser.add_argument('--polygon-pattern', type=str, default='polygon-{id:04d}.svg', help='output file for polygons')

    parser.add_argument('-r', '--run', action='append', default=[], help='plot the run with this id')
    parser.add_argument('--run-pattern', type=str, default='run-{id:08d}.svg', help='output file for runs')

    args = parser.parse_args()

    from matplotlib import pyplot

    from draw import draw_polygon
    from benchmark import model

    if not args.polygon and not args.run:
        print('You have to specify at least one thing to plot.', file=sys.stderr)
        sys.exit(1)

    for id in args.polygon:
        try:
            plot_polygon(int(id), args.polygon_pattern)
        except Exception as e:
            print(e, file=sys.stderr)

    for id in args.run:
        try:
            plot_run(int(id), args.run_pattern)
        except Exception as e:
            print(e, file=sys.stderr)
