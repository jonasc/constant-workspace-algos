"""Some polygon helper classes neede by different modules."""
from typing import Any, Union

from .line_segment import LineSegment
from .point import Point


class PolygonPoint(Point):
    """Extend the point to include an index.

    The index defines the position in the polygon's list of points.
    """

    def __init__(self, x: Union[int, float, Point], y: int = None, index: int = None):
        """Initialize a new polygon point with additional index.

        It can be given either as a point and an index or two coordinates and an
        index.
        """
        if isinstance(x, Point):
            assert isinstance(y, int) or y is None

            self.x = x.x
            self.y = x.y
            self.index = y if y is not None else index
        else:
            assert isinstance(index, int) or index is None

            super(PolygonPoint, self).__init__(x, y)
            self.index = index

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({x!r}, {y!r}, {index!r})'.format(class_=self.__class__.__name__, x=self.x, y=self.y,
                                                          index=self.index)

    def __eq__(self, other: Any) -> bool:
        """Check for equality."""
        # Check point and index equality
        if isinstance(other, PolygonPoint):
            return super(PolygonPoint, self).__eq__(other) and self.index == other.index

        # A simple point can only be equal to an polygon point if the polygon point's index is None
        if isinstance(other, Point):
            if self.index is None:
                return super(PolygonPoint, self).__eq__(other)
            return False

        raise NotImplementedError()


class EdgePoint(Point):
    """Extend the point to include an index.

    The index defines the position in the polygon's list of points.
    """

    def __init__(self, x: Union[int, float, Point], y: int = None, index: int = None):
        """Initialize a new polygon point with additional index.

        It can be given either as a point and an index or two coordinates and an
        index.
        """
        if isinstance(x, Point):
            assert isinstance(y, int) or y is None

            self.x = x.x
            self.y = x.y
            self.index = y if y is not None else index
        else:
            assert isinstance(index, int) or index is None

            super(EdgePoint, self).__init__(x, y)
            self.index = index

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({x!r}, {y!r}, {index!r})'.format(class_=self.__class__.__name__, x=self.x, y=self.y,
                                                          index=self.index)

    def __eq__(self, other: Any) -> bool:
        """Check for equality."""
        # Check point and index equality
        if isinstance(other, EdgePoint):
            return super(EdgePoint, self).__eq__(other) and self.index == other.index

        # A simple point can only be equal to an polygon point if the polygon point's index is None
        if isinstance(other, Point):
            if self.index is None:
                return super(EdgePoint, self).__eq__(other)
            return False

        raise NotImplementedError()


class Edge(LineSegment):
    """Just another name for a line segment."""

    def __eq__(self, other: Any) -> bool:
        """Two edges are equal if the defining points are equal not looking at the direction."""
        if isinstance(other, Edge):
            return (self.a == other.a and self.b == other.b or
                    self.a == other.b and self.b == other.a)

        raise NotImplementedError()
