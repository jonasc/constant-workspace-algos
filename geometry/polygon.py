"""Defines a polygon class with various helper classes and methods."""

from typing import Iterable, List, Optional, Tuple, Union

from .bounded_funnel import BoundedFunnel
from .circle import Circle
from .delaunay_triangle import DelaunayTriangle
from .exceptions import ThreePointsAreCollinearException, TooFewPointsException, NotInGeneralPositionException
from .funnel import Funnel
from .line import Line
from .line_segment import LineSegment
from .point import Point
from .polygon_helper import Edge, EdgePoint, PolygonPoint
from .trapezoid import Trapezoid


class Polygon(object):
    """Defines a polygon in R^2."""

    def __init__(self, points: Union[Iterable[Point], 'Polygon']):
        """O(n): Initialize a new polygon with a list of points.

        The list can be anything which ist convertible to a list when passed to
        the builtin list function. It is furthermore assumed that all objects in
        this list are Point instances.

        We also assume that the points are given in counterclockwise order.
        Otherwise the names of some functions do not make sense.
        """
        if isinstance(points, Polygon):
            points = points.points

        if not isinstance(points, list):
            points = list(points)

        if len(points) < 3:
            raise TooFewPointsException('A polygon needs at least 3 points.')

        for ix, point in enumerate(points):
            assert isinstance(point, Point)
            points[ix] = PolygonPoint(point, ix)

        self.points = tuple(points)
        self.len = len(self.points)

    def points_as_tuples(self) -> Iterable[Tuple[Union[int, float], Union[int, float]]]:
        """O(n): Return a map object of all polygon points as tuples.

        Returns:
            [(int|float, int|float)]: An iterable of tuples (x, y) each consisting of the x- and y-coordinate of each
                point.
        """
        return map(lambda p: p.tuple(), self.points)

    def indices(self, start: int = 0, stop: int = None, step: int = 1) -> Iterable[int]:
        """O(n): Return a generator of all indices between start and stop.

        The indices are returned in the order given, possibly wrapping around
        the highest index to 0.

        You should not set step to anything but 1 or -1.

        Args:
            start: The first index to be returned.
            stop:  The last index to be returned.
            step:  The direction in which to go. (This is added to start until stop is reached)

        Returns:
            [int]: An iterable of integer indices.
        """
        if stop is None:
            stop = self.len - 1

        assert isinstance(start, int)
        assert isinstance(stop, int)
        assert isinstance(step, int)

        start %= self.len
        stop %= self.len

        while start != stop:
            yield start
            start = (start + step) % self.len
        yield start

    def clockwise_indices(self, start: int = None, stop: int = None) -> Iterable[int]:
        """O(n): Return a generator of all indices between start and stop.

        The indices are returned in reversed order, possibly wrapping around the
        highest index to 0.

        Args:
            start: The first index to be returned.
            stop:  The last index to be returned.

        Returns:
            [int]: An iterable of integer indices.
        """
        if start is None:
            start = self.len - 1
        if stop is None:
            stop = 0
        return self.indices(start, stop, -1)

    def prev(self, index: int) -> int:
        """O(1): Return the previous index, possibly wrapping around 0.

        Args:
            index: The index whose predecessor should be returned.

        Returns:
            int: The index preceding the given index.
        """
        assert isinstance(index, int)

        return (index - 1) % self.len

    def next(self, index: int) -> int:
        """O(1): Return the next index, possibly wrapping around the highest.

        Args:
            index: The index whose successor should be returned.

        Returns:
            int: The index succeeding the given index.
        """
        assert isinstance(index, int)

        return (index + 1) % self.len

    def pred(self, point: Union[PolygonPoint, EdgePoint, int]) -> PolygonPoint:
        """O(1): Return the previous point, possibly wrapping around.

        Args:
            point: Either an index or a polygon point whose predecessor should be returned.

        Returns:
            PolygonPoint: The predecessor point.
        """
        assert isinstance(point, (int, PolygonPoint, EdgePoint))

        if isinstance(point, EdgePoint):
            return self.point(point.index)

        if isinstance(point, PolygonPoint):
            return self.point(point.index - 1)

        return self.point(point - 1)

    def succ(self, point: Union[PolygonPoint, EdgePoint, int]) -> PolygonPoint:
        """O(1): Return the next point, possibly wrapping around.

        Args:
            point: Either an index or a polygon point whose successor should be returned.

        Returns:
            PolygonPoint: The successor point.
        """
        assert isinstance(point, (int, PolygonPoint, EdgePoint))

        if isinstance(point, EdgePoint):
            return self.point(point.index + 1)

        if isinstance(point, PolygonPoint):
            return self.point(point.index + 1)

        return self.point(point + 1)

    def point(self, index: int) -> PolygonPoint:
        """O(1): Return the point at a given index.

        Args:
            index: The index of the requested point.

        Returns:
            PolygonPoint: The point whose index is given.
        """
        assert isinstance(index, int)

        return self.points[index % self.len]

    def point_turn(self, p: Union[int, PolygonPoint]) -> int:
        """O(1): Return polygon's turn at the vertex (with index) p."""
        if isinstance(p, PolygonPoint):
            return Point.turn(self.pred(p), p, self.succ(p))

        if isinstance(p, int):
            return self.point_turn(self.point(p))

        raise TypeError()

    def is_concave_point(self, p: Union[int, PolygonPoint]):
        """O(1): Return whether the polygon is concave at the vertex (with index) p."""
        return self.point_turn(p) == Point.CW_TURN

    def is_convex_point(self, p: Union[int, PolygonPoint]):
        """O(1): Return whether the polygon is convex at the vertex (with index) p."""
        return self.point_turn(p) == Point.CCW_TURN

    def edge(self, index: int) -> Edge:
        """O(1): Return the edge starting at the point at the given index.

        The edge goes from point(index) to point(index+1).

        Args:
            index: The index of the edge's starting point.

        Returns:
            Edge: The edge going from point(index) to point(next(index)).
        """
        assert isinstance(index, int)

        return Edge(self.point(index), self.point(index + 1))

    def edges(self) -> Iterable[Edge]:
        """O(n): Return an iterable of all polygon edges.

        Returns:
            [Edge]: An iterable of all polygon edges
        """
        for ix in self.indices():
            yield self.edge(ix)

    def _is_in_general_position(self) -> bool:
        for a_ix in range(len(self)):
            for b_ix in range(a_ix + 1, len(self)):
                for c_ix in range(b_ix + 1, len(self)):
                    if Point.turn(self.point(a_ix), self.point(b_ix), self.point(c_ix)) == Point.NO_TURN:
                        return False

        return True

    def complete_delaunay_edge(self, edge: Union[Edge, PolygonPoint], b: PolygonPoint = None
                               ) -> Tuple[Optional[PolygonPoint], Optional[PolygonPoint]]:
        """O(n^2): Compute the missing vertex/vertices for (a) delaunay triangle(s).

        Given an edge or two points return the third point constituting a triangle in the contrained delaunay
        triangulation. If the edge is not a polygon boundary itself, it is part of two triangles and thus two points
        are ALWAYS returned.

        Args:
            edge: Either an edge whose completing delaunay edges should be given OR the first point of an edge.
            b:    Either null (iff edge is an edge) OR the second point of an edge.

        Returns:
            (PolygonPoint, PolygonPoint): A tuple consisting of two polygon points (each can be None) the first one
                lying on the left side of the given edge, the second one on the right side.
        """
        assert ((isinstance(edge, Edge) and b is None) or
                (isinstance(edge, PolygonPoint) and isinstance(b, PolygonPoint)))

        if isinstance(edge, PolygonPoint):
            a = edge
            edge = Edge(a, b)
        else:
            a = edge.a
            b = edge.b

        a_prev = self.point(a.index - 1)
        a_next = self.point(a.index + 1)
        b_prev = self.point(b.index - 1)
        b_next = self.point(b.index + 1)

        # Use funnels to check whether new edges lie inside the polygon
        a_funnel = Funnel(a, a_next, a_prev)
        b_funnel = Funnel(b, b_next, b_prev)

        # logging.info('Finding the third delaunay vertex for %s', edge)

        best = [None, None]
        best_circle = [None, None]

        for curr_index, curr in enumerate(self.points):
            # Skip if current point is one of the given ones
            if curr == a or curr == b:
                continue
            # Check whether the new edge lies inside the polygon
            if not a_funnel.contains(curr):
                continue
            if not b_funnel.contains(curr):
                continue

            position = Point.turn(a, b, curr)
            if position == Point.NO_TURN:
                raise ThreePointsAreCollinearException(a, b, curr)
            which = 1
            if position == Point.CCW_TURN:
                which = 0

            # Check whether current point is the first or better than the
            # current best
            if best[which] is None or best_circle[which].contains(curr):
                # logging.info('%s is a completion candidate', curr)
                better = True

                a_edge = Edge(a, curr)
                b_edge = Edge(b, curr)

                # Check visibility of current point
                for ix in self.indices():
                    border = self.edge(ix)
                    # logging.debug('Checking for border intersection with %s',
                    #               border)

                    # Check for intersection of the new edge with the border
                    if border.properly_intersects(a_edge) or border.properly_intersects(b_edge):
                        better = False
                        break

                if better:
                    try:
                        # logging.info('Found new best %s', curr)
                        best_circle[which] = Circle(a, b, curr)
                        best[which] = curr
                    except ThreePointsAreCollinearException:
                        pass

        return tuple(best)

    def _find_edges_above_and_below(self, p: Point) -> Optional[Tuple[int, int]]:
        """O(n): Return the indices of the nearest edges above and below the given point (in this order).

        Args:
            p: The point whose top and bottom edge indices should be found.

        Returns:
            (int, int) or None: Returns None if not both edges can be found and otherwise the indices in the order
                (top_edge_index, bottom_edge_index).
        """
        distance_below, distance_above = None, None
        top_edge_index, bottom_edge_index = None, None
        top_node, bottom_node = None, None

        for curr_index, curr in enumerate(self.points):
            next_ = self.point(curr_index + 1)

            # Ignore edges not covering the x-coordinate of our point
            if p.x < min(curr.x, next_.x) or p.x > max(curr.x, next_.x):
                continue

            if p.x == curr.x:
                if curr.y < p.y and (bottom_node is None or curr.y > bottom_node.y):
                    bottom_node = curr
                elif curr.y > p.y and (top_node is None or curr.y > top_node.y):
                    top_node = curr

            # Get the edge's y-coordinate with the point's x-coordinate
            y_on_edge = Line.y_value(curr, next_, p.x)

            # We may have found an edge closer to our point but we only take correct edges
            if y_on_edge < p.y and (distance_below is None or p.y - y_on_edge < distance_below):
                # The edge's left side is the polygon's inside, thus we only take bottom edges from left to right
                if curr.x < next_.x:
                    bottom_edge_index = curr_index
                    distance_below = p.y - y_on_edge
                else:
                    # We reset the bottom edge iff the closest bottom edge leaves us on the outside
                    bottom_edge_index = None
            if y_on_edge > p.y and (distance_above is None or y_on_edge - p.y < distance_above):
                # The edge's left side is the polygon's inside, thus we only take top edges from right to left
                if curr.x > next_.x:
                    top_edge_index = curr_index
                    distance_above = y_on_edge - p.y
                else:
                    # We reset the top edge iff the closest top edge leaves us on the outside
                    top_edge_index = None

        if top_node is not None and bottom_node is not None:
            raise NotInGeneralPositionException()

        if top_edge_index is None and top_node is not None:
            if Point.turn(top_node, self.succ(top_node), p) != Point.CW_TURN:
                top_edge_index = top_node.index
            else:
                top_edge_index = self.prev(top_node.index)

        if bottom_edge_index is None and bottom_node is not None:
            if Point.turn(self.pred(bottom_node), bottom_node, p) != Point.CW_TURN:
                bottom_edge_index = self.prev(bottom_node.index)
            else:
                bottom_edge_index = bottom_node.index

        if top_edge_index is None or bottom_edge_index is None:
            return None, None

        assert self.point(top_edge_index).x > self.point(top_edge_index + 1).x
        assert self.point(bottom_edge_index).x < self.point(bottom_edge_index + 1).x

        return top_edge_index, bottom_edge_index

    def trapezoid(self, p: Point) -> Optional[Trapezoid]:
        """O(n): Return the trapezoid in which the point p ist located.

        The runtime is O(n) where n is the polygon's size (i.e. number of
        vertices).

        Args:
            p: The point for which the containing trapezoid ist requested.

        Returns:
            Trapezoid or None: The trapezoid containing p or None if p lies outside of the polygon.
        """
        # logging.info('Locating %s inside polygon', p)
        assert isinstance(p, Point)

        v_top_left_ix, v_top_right_ix = None, None
        v_bot_left_ix, v_bot_right_ix = None, None

        # Find the top and bottom edges
        top_edge_ix, bot_edge_ix = self._find_edges_above_and_below(p)

        if top_edge_ix is None or bot_edge_ix is None:
            return None

        # Get the top and bottom endpoints of the edges
        v_top_left = self.point(top_edge_ix + 1)
        v_top_right = self.point(top_edge_ix)
        assert v_top_right.is_right_of(v_top_left)

        v_bot_left = self.point(bot_edge_ix)
        v_bot_right = self.point(bot_edge_ix + 1)
        assert v_bot_right.is_right_of(v_bot_left)

        # Save only the (two out of four) edge endpoints that really define the trapezoid
        if v_top_left.is_right_of(v_bot_left):
            left = v_top_left
            v_top_left_ix = v_top_left.index
        elif v_bot_left.is_right_of(v_top_left):
            left = v_bot_left
            v_bot_left_ix = v_bot_left.index
        else:
            left = v_bot_left
            v_top_left_ix = v_top_left.index
            v_bot_left_ix = v_bot_left.index

        if v_top_right.left_of(v_bot_right):
            right = v_top_right
            v_top_right_ix = v_top_right.index
        elif v_bot_right.left_of(v_top_right):
            right = v_bot_right
            v_bot_right_ix = v_bot_right.index
        else:
            right = v_bot_right
            v_top_right_ix = v_top_right.index
            v_bot_right_ix = v_bot_right.index

        top_line = Line(v_top_left, v_top_right)
        bot_line = Line(v_bot_left, v_bot_right)

        for curr_index, curr in enumerate(self.points):
            if (curr.is_right_of(left) and curr.left_of(p) and
                    not self.points[self.prev(curr_index)].is_right_of(curr) and
                    not self.points[self.next(curr_index)].is_right_of(curr) and
                    bot_line.y(curr.x) <= curr.y <= top_line.y(curr.x)):
                left = curr
                v_top_left_ix, v_bot_left_ix = None, None
                # logging.debug('%s schränkt von links ein', curr)
            if (curr.left_of(right) and curr.is_right_of(p) and
                    not self.points[self.prev(curr_index)].left_of(curr) and
                    not self.points[self.next(curr_index)].left_of(curr) and
                    bot_line.y(curr.x) <= curr.y <= top_line.y(curr.x)):
                right = curr
                v_top_right_ix, v_bot_right_ix = None, None
                # logging.debug('%s schränkt von rechts ein', curr)

        x_left = left.x
        x_right = right.x
        y_left1 = v_top_left.y if x_left == v_top_left.x else top_line.y(x_left)
        y_right1 = v_top_right.y if x_right == v_top_right.x else top_line.y(x_right)
        y_left2 = v_bot_left.y if x_left == v_bot_left.x else bot_line.y(x_left)
        y_right2 = v_bot_right.y if x_right == v_bot_right.x else bot_line.y(x_right)

        return Trapezoid(x_left, x_right, y_left1, y_right1, y_left2, y_right2,
                         top_edge_ix, bot_edge_ix, v_top_left_ix, v_bot_left_ix,
                         v_top_right_ix, v_bot_right_ix)

    def neighbour_trapezoids(self, t: Trapezoid, which: int = 0b11) -> List[Trapezoid]:
        """O(n): Return all trapezoids neighbouring the given trapezoid.

        The runtime is O(n) where n is the polygon's size (i.e. number of
        vertices). This is only true iff we can assume a constant number of
        neighbours. It is true if all vertices' x-coordinates differ.

        Args:
            t:     The trapezoid whose neighbours are to be found.
            which: Combinations of two bits specifying on which side of the trapezoid to look. 0b01 means "on the right"
                and 0b10 means "on the left".

        Returns:
            [Trapezoid]: A list of trapezoids neighbouring t according to which.
        """
        # logging.debug('Getting all neighbour trapezoids of %s', t)
        assert isinstance(t, Trapezoid)

        dist = 1e-6

        top_left, bot_left, top_right, bot_right = None, None, None, None

        try:
            if which & 0b10:
                if t.top_left_ix is None:
                    line = Line(self.point(t.top_edge_ix), self.point(t.top_edge_ix + 1))
                else:
                    line = Line(self.point(t.top_left_ix), self.point(t.top_left_ix + 1))
                top_left = self.trapezoid(
                    Point(t.x_left - dist, line.y(t.x_left - dist) - dist))

                if t.bot_left_ix is None:
                    line = Line(self.point(t.bot_edge_ix), self.point(t.bot_edge_ix + 1))
                else:
                    line = Line(self.point(t.bot_left_ix - 1), self.point(t.bot_left_ix))
                bot_left = self.trapezoid(
                    Point(t.x_left - dist, line.y(t.x_left - dist) + dist))

            if which & 0b01:
                if t.top_right_ix is None:
                    line = Line(self.point(t.top_edge_ix), self.point(t.top_edge_ix + 1))
                else:
                    line = Line(self.point(t.top_right_ix - 1),
                                self.point(t.top_right_ix))
                top_right = self.trapezoid(
                    Point(t.x_right + dist, line.y(t.x_right + dist) - dist))

                if t.bot_right_ix is None:
                    line = Line(self.point(t.bot_edge_ix), self.point(t.bot_edge_ix + 1))
                else:
                    line = Line(self.point(t.bot_right_ix),
                                self.point(t.bot_right_ix + 1))
                bot_right = self.trapezoid(
                    Point(t.x_right + dist, line.y(t.x_right + dist) + dist))
        except ValueError:
            raise NotInGeneralPositionException()

        res = []

        if which & 0b10 and top_left is not None:
            res.append(top_left)

        if which & 0b10 and top_left != bot_left and bot_left is not None:
            res.append(bot_left)

        if which & 0b01 and bot_right is not None:
            res.append(bot_right)

        if which & 0b01 and top_right != bot_right and top_right is not None:
            res.append(top_right)

        # logging.debug('The neighbour(s) is/are %s', res)
        return res

    def point_sees_edge(self, point: Point, edge: Edge) -> Tuple[bool, Optional[Point], Optional[Point]]:
        """O(n): Check whether the point can see the edge in the polygon.

        We need to check all polygon edges once, thus the runtime is O(n) where
        n is the polygon's size (i.e. number of vertices).

        Args:
            point: The point that should see the edge.
            edge:  The edge that should be seen by the point.

        Returns:
            (bool, Point|None, Point|None): a tuple consisting of a boolean specifying whether point sees edge and (in
                case of visibility) the two points which inhibit the visibility from right and left.
        """
        assert isinstance(point, Point)
        assert isinstance(edge, Edge)

        # If one of the edge points is the point itself just return True
        if point == edge.a:
            return True, edge.a, edge.b
        if point == edge.b:
            return True, edge.b, edge.a

        # The initial funnel
        if Point.turn(point, edge.a, edge.b) == Point.CCW_TURN:
            edge_first, edge_second = edge.a, edge.b
        else:
            edge_first, edge_second = edge.b, edge.a

        # Special case: if the edge is a polygon edge and we need to rotate it, we cannot see it.
        if isinstance(edge.a, PolygonPoint) and isinstance(edge.b, PolygonPoint):
            if edge.b.index is not None and edge.a.index is not None:
                if edge.a.index in (edge.b.index - 1, edge.b.index + 1):
                    if edge_first == edge.b:
                        return False, None, None

        funnel = Funnel(point, edge_first, edge_second)

        funnels = None

        # If the point is a polygon point we first check whether the two
        # neighbouring edges prevent visibility -- if we do not do this there
        # are special cases that might fail
        if isinstance(point, PolygonPoint):
            if point.index is not None:
                # If the point is concave we need to treat it differently
                if self.is_concave_point(point):
                    # Construct a funnel using the vertex's neighbouring edges
                    point_funnel = Funnel(point, self.succ(point), self.pred(point))

                    # There is a special situation in which the point-funnel contains both end points but not the edge
                    # In this case we need to look at two funnels
                    if point_funnel.contains(edge_first) and point_funnel.contains(edge_second) and \
                            not point_funnel.contains(edge):
                        funnels = [
                            BoundedFunnel(point, self.succ(point), edge_second, edge_first, edge_second),
                            BoundedFunnel(point, edge_first, self.pred(point), edge_first, edge_second)
                        ]

                if funnels is None:
                    # Construct a funnel using the vertex's neighbouring edges
                    point_funnel = Funnel(point, self.succ(point), self.pred(point))
                    # At least one of the points should be contained in the other funnel
                    if not (point_funnel.contains(funnel.first) or
                            point_funnel.contains(funnel.second) or
                            funnel.contains(point_funnel.first) or
                            funnel.contains(point_funnel.second)
                            ):
                        return False, None, None

                    # Use the point funnel and shrink it to the maximal size with the given boundary.
                    if funnel.contains(self.succ(point)):
                        funnel.first = self.succ(point)

                    if funnel.contains(self.pred(point)):
                        funnel.second = self.pred(point)

                    if funnel.first == funnel.second:
                        return False, None, None

        if funnels is None:
            funnels = [BoundedFunnel(funnel.cusp, funnel.first, funnel.second, edge_first, edge_second)]

        # First we need to find an edge which is not completely contained inside
        # the visibility cone. This is because otherwise we would have to split
        # up the cone into two parts.
        # This takes O(n) time.
        for start_ix in self.indices():
            all = True
            for funnel in funnels:
                if funnel.contains(self.edge(start_ix)):
                    all = False
                    break
            if all:
                break

        # Go through all polygon edges and check whether they prevent visibility
        for ix in self.indices(start_ix, start_ix - 1):
            p_edge = self.edge(ix)

            # If we have a right turn reverse the edge
            p_first = p_edge.a
            p_second = p_edge.b
            if Point.turn(point, p_edge.a, p_edge.b) == Point.CW_TURN:
                p_first, p_second = p_second, p_first

            for funnel in funnels[:]:
                assert not funnel.properly_contains(p_edge)

                if funnel.properly_contains(p_first):
                    funnel.second = p_first

                if funnel.properly_contains(p_second):
                    funnel.first = p_second

                if funnel.is_half_properly_divided_by(p_edge):
                    funnels.remove(funnel)

                if (funnel.first == p_first and funnel.second == p_second and funnel.contains(p_first) and
                        funnel.contains(p_second)):
                    # do not remove if the boundary is the edge we see
                    if p_first != edge_first or p_second != edge_second:
                        funnels.remove(funnel)

                if funnel.first == funnel.second:
                    funnels.remove(funnel)

            if len(funnels) == 0:
                return False, None, None

        assert len(funnels) == 1

        return True, funnels[0].first, funnels[0].second

    def point_sees_edge2(self, point: Point, edge: Edge) -> Union[bool, Tuple[Point, Point]]:
        """O(n): Check whether the point can see the edge in the polygon.

        We need to check all polygon edges once, thus the runtime is O(n) where n is the polygon's size (i.e. number of
        vertices).

        Args:
            point: The point that should see the edge.
            edge:  The edge that should be seen by the point.

        Returns:
            bool|(Point, Point): Either false if point does not see edge or a tuple consisting of the two points which
                inhibit the visibility from right and left.
        """
        (r, a, b) = self.point_sees_edge(point, edge)
        if r:
            return a, b
        return False

    def point_sees_other_point(self, point: Point, other_point: Point) -> bool:
        """O(n): Check whether point can see other_point in the polygon.

        We need to check all polygon edges once, thus the runtime is O(n) where
        n is the polygon's size (i.e. number of vertices).

        Args:
            point:       The first point.
            other_point: The second point.

        Returns:
            bool: True iff the line segment from point to other_point does not cross the polygon boundaries.
        """
        assert isinstance(point, Point)
        assert isinstance(other_point, Point)

        edge = LineSegment(point, other_point)

        # Go through all polygon edges and check whether they intersect the
        # visibility line
        for ix in self.indices():
            if edge.properly_intersects(self.edge(ix)):
                return False

        return True

    def point_inside_at(self, index: int, round: bool = True) -> Point:
        """O(n^2): Return a point that lies inside the polygon near the given edge.

        We compute the center of the corresponding delaunay triangle so it takes quadratic time.

        Args:
            index: The index of the edge at which the point should be located.

        Returns:
            Point: A point inside the polygon near the edge with the given index.
        """
        a = self.point(index)
        b = self.point(index + 1)
        c = self.complete_delaunay_edge(a, b)[0]

        p = Point((a.x + b.x + c.x) / 3, (a.y + b.y + c.y) / 3)

        if not round:
            return p

        q = None
        digits = 4
        triangle = DelaunayTriangle(a, b, c)

        while q is None or not triangle.contains(q):
            q = Point(p.x, p.y).round(digits)
            digits += 1

        return q

    def delaunay_first_neighbour(self, triangle: DelaunayTriangle) -> Optional[DelaunayTriangle]:
        """O(n^2): Return the first neighbouring triangle to a given one.

        Args:
            triangle: The delaunay triangle whose first neighbour should be retrieved.

        Returns:
            DelaunayTriangle|None: The first delaunay triangle in triangle edge order if the given triangle has a
                neighbouring triangle. If no neighbour exists it returns None.
        """
        assert isinstance(triangle, DelaunayTriangle)

        for edge in triangle.edges:
            neighbour = self._complete_other_delaunay_triangle_of_edge(edge, triangle)
            if neighbour is not None:
                return neighbour

        return None

    def delaunay_next_neighbour(self, triangle: DelaunayTriangle, neighbour: DelaunayTriangle
                                ) -> Optional[DelaunayTriangle]:
        """O(n^2): Return `triangle`'s next neighbour after `neighbour`.

        Args:
            triangle:  The triangle whose next neighbour should be found.
            neighbour: The existing neighbour at which search is started.

        Returns:
            DelaunayTriangle|None: The next delaunay triangle when walking the triangle edges starting at edge after the
                common edge if triangle and neighbour.
        """
        assert isinstance(triangle, DelaunayTriangle)
        assert isinstance(neighbour, DelaunayTriangle)

        common_edge = triangle.common_edge(neighbour)
        assert common_edge is not None

        for edge in triangle.edges_until(common_edge):
            next_neighbour = self._complete_other_delaunay_triangle_of_edge(edge, triangle)
            if next_neighbour is not None:
                return next_neighbour

        return None

    def _complete_other_delaunay_triangle_of_edge(self, edge: Edge, triangle: DelaunayTriangle
                                                  ) -> Optional[DelaunayTriangle]:
        """O(n^2): Return delaunay triangle completing `edge` which is not `triangle`.

        Args:
            edge:     The edge whose delaunay triangle should be found.
            triangle: A delaunay triangle which has edge as one of its edges.

        Returns:
            DelaunayTriangle|None: If edge has two neighbouring delaunay triangles the one not being triangle is
                returned. Otherwise None is returned.
        """
        assert isinstance(edge, Edge)
        assert isinstance(triangle, DelaunayTriangle)
        assert edge in triangle.edges

        # Get the (hopefully) two points
        points = self.complete_delaunay_edge(edge)

        if points[0] is None or points[1] is None:
            return None

        if points[0] in triangle.points:
            return DelaunayTriangle(points[1], edge.a, edge.b)
        if points[1] in triangle.points:
            return DelaunayTriangle(points[0], edge.a, edge.b)

        assert False

    def delaunay_neighbour_number(self, triangle: DelaunayTriangle) -> int:
        """O(1): Return the number of neighbours `triangle` has.

        We just check for every edge whether the endpoints are directly following each other.

        Args:
            triangle: The triangle to check.

        Returns:
            int: The number of neighbours.
        """
        neighbours = 0
        for edge in triangle.edges:
            # Only count non-polygon-edge borders
            if edge.a.index - edge.b.index not in (-1, 1):
                neighbours += 1

        return neighbours

    def locate_point_in_triangle(self, p: Point) -> Optional[DelaunayTriangle]:
        """O(n^3): Find delaunay triangle in which the given point is located.

        Args:
            p: The point which should be located.

        Returns:
            DelaunayTriangle|None: The triangle in which `p` is located. None if `p` is outside of the polygon.
        """
        assert isinstance(p, Point)

        # First we find the nearest edge hitting a ray shot directly upwards from p
        edges = self._find_edges_above_and_below(p)
        if edges[0] is None or edges[1] is None:
            return None

        # We then construct the first triangle
        start_edge = self.edge(edges[0])
        points = self.complete_delaunay_edge(start_edge)
        assert points[1] is None
        assert points[0] is not None

        triangle = DelaunayTriangle(self.point(edges[0]), self.point(edges[0] + 1), points[0])

        # Step by step we will reach out point
        while not triangle.contains(p):
            # Find the edge of the triangle nearest to our point that covers our point's x-coordinate
            next_edge = None
            for edge in triangle.edges:
                if edge == start_edge:
                    continue

                if edge.a.x <= p.x <= edge.b.x or edge.b.x <= p.x <= edge.a.x:
                    next_edge = edge
                    break

            # Make sure we always find an edge
            assert next_edge is not None
            start_edge = next_edge

            # Find next delaunay triangle for this edge
            triangle = self._complete_other_delaunay_triangle_of_edge(next_edge, triangle)
            assert triangle is not None

        return triangle

    def __repr__(self) -> str:
        """Return nice string representation for console."""
        return '{class_}({points!r})'.format(class_=self.__class__.__name__, points=self.points)

    def __len__(self) -> int:
        """Return the length of the polygon (i.e. the number of vertices)."""
        return self.len

    def __eq__(self, other) -> bool:
        """Check whether two polygons are equal (ignoring rotation)."""
        if isinstance(other, Polygon):
            if len(self) != len(other):
                return False

            for start, p in enumerate(other.points):
                if p.tuple() == self.points[0].tuple():
                    break
            else:
                return False

            for i, p in enumerate(self.points):
                if p.tuple() != other.points[(i + start) % len(other)].tuple():
                    return False

            return True

        return NotImplemented
