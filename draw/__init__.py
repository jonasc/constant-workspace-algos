"""Collection of drawing functions."""
from math import ceil, floor

from matplotlib import pyplot, ticker
from matplotlib.axes import Axes

from defaults import font_size, size, ticks
from geometry import TriangulatedPolygon
from geometry.polygon import Polygon


def draw_polygon(ax: Axes, polygon: Polygon, size: int = size, ticks: int = ticks, font_size: int = font_size) -> None:
    """Plot a polygon to the current matplotlib figure."""
    max_x, min_x = ceil(max(p.x for p in polygon.points)), floor(min(p.x for p in polygon.points))
    max_y, min_y = ceil(max(p.y for p in polygon.points)), floor(min(p.y for p in polygon.points))
    size_x = max_x - min_x
    size_y = max_y - min_y
    ax.set_aspect('equal')
    ax.set_xlim(min_x - size_x * 0.05, max_x + size_x * 0.05)
    ax.set_ylim(min_y - size_y * 0.05, max_y + size_y * 0.05)
    ticks -= 1
    ax.xaxis.set_major_locator(ticker.MultipleLocator(base=round(size_x / ticks)))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(base=round(size_y / ticks)))
    ax.grid(color='grey')

    polygon_points = list(polygon.points_as_tuples())

    plt_polygon = pyplot.Polygon(polygon_points, fill=None, color='0.25', linewidth=.5)
    ax.add_patch(plt_polygon)
    pyplot.plot(list([x[0] for x in polygon_points]), list([x[1] for x in polygon_points]),
                color='black', linestyle='None', marker='.', markersize=3)

    if isinstance(polygon, TriangulatedPolygon):
        edges = set()
        for triangle in polygon.triangles:
            for edge in triangle.edges:
                if (edge.a.index, edge.b.index) in edges:
                    # The edge was already plotted
                    continue
                if edge.a.index in ((edge.b.index - 1) % len(polygon), (edge.b.index + 1) % len(polygon)):
                    # The edge is a polygon edge, thus we ignore it
                    continue

                pyplot.plot([edge.a.x, edge.b.x], [edge.a.y, edge.b.y], color='0.5', linestyle='--', alpha=0.5)
                edges.add((edge.a.index, edge.b.index))
                edges.add((edge.b.index, edge.a.index))

    for i in range(0, len(polygon), 2):
        ax.annotate(str(i), xy=polygon_points[i],
                    xytext=(
                        polygon_points[i][0] + round(size_x / ticks) / 20,
                        polygon_points[i][1] + round(size_y / ticks) / 20),
                    fontsize=font_size, color='0.3', alpha=.8)
