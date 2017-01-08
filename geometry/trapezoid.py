"""Defines a trapezoid class with various helper classes and methods."""
from typing import Any, List, Optional, Tuple, Union

from .polygon_helper import Edge, PolygonPoint


class IntersectionPoint(PolygonPoint):
    """A polygon point with additional information about the edge it lies on."""

    def __init__(self, *args, **kwargs):
        """Initialize a new intersection point."""
        self.edge = None
        if 'edge' in kwargs:
            assert isinstance(kwargs['edge'], int) or kwargs['edge'] is None
            self.edge = kwargs['edge']
            del kwargs['edge']

        super(IntersectionPoint, self).__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({x!r}, {y!r}, {index!r}, edge={edge!r})'.format(class_=self.__class__.__name__, x=self.x,
                                                                         y=self.y, index=self.index, edge=self.edge)


class Trapezoid(object):
    """Defines a trapezoid in R^2."""

    def __init__(self, x_left: Union[int, float], x_right: Union[int, float], y_left1: Union[int, float],
                 y_right1: Union[int, float], y_left2: Union[int, float], y_right2: Union[int, float],
                 top_edge_ix: int, bot_edge_ix: int,
                 top_left_ix: int = None, bot_left_ix: int = None, top_right_ix: int = None, bot_right_ix: int = None):
        """Initialize a new trapezoid.

        This is a trapezoid with the left and right edges being parallel to the
        y-axis.
        Additionally indices of the points and top and bottom edges
        corresponding to the vertices and edges of the polygon are stored.
        """
        # TODO: Add assertions about parameters

        # x-value of the left vertical boundary
        self.x_left = x_left
        # x-value of the right vertical boundary
        self.x_right = x_right
        # y-value of the top left vertex
        self.y_left1 = y_left1
        # y-value of the top right vertex
        self.y_right1 = y_right1
        # y-value of the bottom left vertex
        self.y_left2 = y_left2
        # y-value of the bottom right vertex
        self.y_right2 = y_right2
        # edge index of the top edge
        self.top_edge_ix = top_edge_ix
        # edge index of the bottom edge
        self.bot_edge_ix = bot_edge_ix

        self.top_left_ix = top_left_ix
        self.bot_left_ix = bot_left_ix
        self.top_right_ix = top_right_ix
        self.bot_right_ix = bot_right_ix

    def as_polygon_tuple(self) -> List[Tuple[Union[int, float], Union[int, float]]]:
        """Return the four vertex points as a list of (x,y)-tuples."""
        return [
            (self.x_left, self.y_left1),
            (self.x_left, self.y_left2),
            (self.x_right, self.y_right2),
            (self.x_right, self.y_right1),
        ]

    def is_triangle(self) -> bool:
        """Check whether the trapezoid actually is a triangle."""
        return self.y_left1 == self.y_left2 or self.y_right1 == self.y_right2

    def is_right_of(self, t: 'Trapezoid') -> bool:
        """Return true if from t we go to the right to reach this trapezoid."""
        assert isinstance(t, Trapezoid)

        if t.top_edge_ix > t.bot_edge_ix:
            return (
                t.top_edge_ix >= self.top_edge_ix >= t.bot_edge_ix and
                t.top_edge_ix >= self.bot_edge_ix >= t.bot_edge_ix
            )
        else:
            return not (
                t.top_edge_ix < self.top_edge_ix < t.bot_edge_ix or
                t.top_edge_ix < self.bot_edge_ix < t.bot_edge_ix
            )

    def is_left_of(self, t: 'Trapezoid') -> bool:
        """Return true if from t we go to the left to reach this trapezoid."""
        assert isinstance(t, Trapezoid)

        if t.top_edge_ix < t.bot_edge_ix:
            return (
                t.top_edge_ix <= self.top_edge_ix <= t.bot_edge_ix and
                t.top_edge_ix <= self.bot_edge_ix <= t.bot_edge_ix
            )
        else:
            return not (
                t.top_edge_ix > self.top_edge_ix > t.bot_edge_ix or
                t.top_edge_ix > self.bot_edge_ix > t.bot_edge_ix
            )

    def intersection(self, trapezoid: 'Trapezoid') -> Optional[Edge]:
        """Return the edge between two trapezoids if it exists, else None."""
        assert isinstance(trapezoid, Trapezoid)

        if self.x_right == trapezoid.x_left:
            first_edge = None
            if trapezoid.y_left1 < self.y_right1:
                first_index = trapezoid.top_left_ix
                if first_index is None:
                    first_edge = trapezoid.top_edge_ix
            else:
                first_index = self.top_right_ix
                if first_index is None:
                    first_edge = self.top_edge_ix

            second_edge = None
            if trapezoid.y_left2 > self.y_right2:
                second_index = trapezoid.bot_left_ix
                if second_index is None:
                    second_edge = trapezoid.bot_edge_ix
            else:
                second_index = self.bot_right_ix
                if second_index is None:
                    second_edge = self.bot_edge_ix

            first = IntersectionPoint(
                self.x_right,
                min(self.y_right1, trapezoid.y_left1),
                first_index,
                edge=first_edge
            )
            second = IntersectionPoint(
                self.x_right,
                max(self.y_right2, trapezoid.y_left2),
                second_index,
                edge=second_edge
            )

            return Edge(first, second)

        if self.x_left == trapezoid.x_right:
            first_edge = None
            if trapezoid.y_right1 < self.y_left1:
                first_index = trapezoid.top_right_ix
                if first_index is None:
                    first_edge = trapezoid.top_edge_ix
            else:
                first_index = self.top_left_ix
                if first_index is None:
                    first_edge = self.top_edge_ix

            second_edge = None
            if trapezoid.y_right2 > self.y_left2:
                second_index = trapezoid.bot_right_ix
                if second_index is None:
                    second_edge = trapezoid.bot_edge_ix
            else:
                second_index = self.bot_left_ix
                if second_index is None:
                    second_edge = self.bot_edge_ix

            first = IntersectionPoint(
                self.x_left,
                min(self.y_left1, trapezoid.y_right1),
                first_index,
                edge=first_edge
            )
            second = IntersectionPoint(
                self.x_left,
                max(self.y_left2, trapezoid.y_right2),
                second_index,
                edge=second_edge
            )

            return Edge(first, second)

        return None

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return (
            '{class_}(x_left={x_left!r}, y_left1={y_left1!r}, y_left2={y_left2!r}, x_right={x_right!r}, '
            'y_right1={y_right1!r}, y_right2={y_right2!r}, top_edge_ix={top_edge_ix!r}, bot_edge_ix={bot_edge_ix!r}, '
            'top_left_ix={top_left_ix!r}, bot_left_ix={bot_left_ix!r}, bot_right_ix={bot_right_ix!r}, '
            'top_right_ix={top_right_ix!r})').format(
            class_=self.__class__.__name__, x_left=self.x_left, y_left1=self.y_left1, y_left2=self.y_left2,
            x_right=self.x_right, y_right1=self.y_right1, y_right2=self.y_right2, top_edge_ix=self.top_edge_ix,
            bot_edge_ix=self.bot_edge_ix, top_left_ix=self.top_left_ix, bot_left_ix=self.bot_left_ix,
            bot_right_ix=self.bot_right_ix, top_right_ix=self.top_right_ix)

    def __eq__(self, t: Any) -> bool:
        """Check equality of two trapezoids."""
        return (
            isinstance(t, Trapezoid) and
            self.x_left == t.x_left and self.x_right == t.x_right and
            self.y_left1 == t.y_left1 and self.y_left2 == t.y_left2 and
            self.y_right1 == t.y_right1 and self.y_right2 == t.y_right2
        )
