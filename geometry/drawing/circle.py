"""Implements a drawable circle."""

from matplotlib.pyplot import Circle as DrawCircle, draw, gca

from ..circle import Circle as OriginalCircle


class Circle(OriginalCircle):
    """Defines a circle in R^2.

    This circle is drawable.
    """

    def __init__(self, *args, squared: bool = False, **kwargs):
        """Initialize a new circle.

        The circle can be given either as three (non-colinear) points or as a
        point an a (potentially squared) radius.
        """
        super(Circle, self).__init__(*args, squared=squared)

        if 'color' not in kwargs:
            kwargs['color'] = 'grey'
        if 'fill' not in kwargs:
            kwargs['fill'] = True
        if 'zorder' not in kwargs:
            kwargs['zorder'] = 50
        if 'alpha' not in kwargs:
            kwargs['alpha'] = .2

        self.circle = DrawCircle(self.center.tuple(), self.radius, **kwargs)
        gca().add_patch(self.circle)
        draw()

    @OriginalCircle.radius.setter
    def radius(self, value: float) -> None:
        """Set the radius of the circle."""
        super(Circle, self.__class__).radius.__set__(self, value)

        self.circle.set_radius(self.radius)
        draw()

    @OriginalCircle.radius2.setter
    def radius2(self, value: float) -> None:
        """Set the squared radius of the circle."""
        super(Circle, self.__class__).radius2.__set__(self, value)

        self.circle.set_radius(self.radius)
        draw()
