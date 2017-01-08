"""Implements a drawable funnel."""
from matplotlib.axes import Axes
from matplotlib.pyplot import Polygon, draw, gca

from ..funnel import Funnel as OriginalFunnel
from ..point import Point


class Funnel(OriginalFunnel):
    """Defines a funnel (an angular region defined by three points) in R^2.

    This funnel is drawable.
    """

    def __init__(self, cusp: Point, first: Point, second: Point, *args, **kwargs):
        """Initialize a new funnel given by three points."""
        super(Funnel, self).__init__(cusp, first, second)

        if 'color' not in kwargs:
            kwargs['color'] = 'red'
        if 'fill' not in kwargs:
            kwargs['fill'] = None
        kwargs['closed'] = False
        if 'zorder' not in kwargs:
            kwargs['zorder'] = 10

        self.polygon = Polygon([
            (first + (first - cusp) * 10).tuple(),
            cusp.tuple(),
            (second + (second - cusp) * 10).tuple()
        ], *args, **kwargs)
        gca().add_patch(self.polygon)
        draw()

    @OriginalFunnel.first.setter
    def first(self, value: Point) -> None:
        """Set the first boundary point."""
        super(Funnel, self.__class__).first.__set__(self, value)
        self._update_polygon()

    @OriginalFunnel.second.setter
    def second(self, value: Point) -> None:
        """Set the second boundary point."""
        super(Funnel, self.__class__).second.__set__(self, value)
        self._update_polygon()

    @OriginalFunnel.cusp.setter
    def cusp(self, value: Point) -> None:
        """Set the second boundary point."""
        super(Funnel, self.__class__).cusp.__set__(self, value)
        self._update_polygon()

    def _update_polygon(self) -> None:
        xy = [
            (self._first + (self._first - self._cusp) * 10).tuple(),
            self._cusp.tuple(),
            (self._second + (self._second - self._cusp) * 10).tuple()
        ]
        self.polygon.set_xy(xy)
        draw()

    def draw(self, axes: Axes) -> None:
        """Add the drawable polygon to the given matplotlib object."""
        axes.add_patch(self.polygon)
