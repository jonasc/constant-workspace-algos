"""Calculate the geodesic shortest path in a polygon.

Asano, Tetsuo, Wolfgang Mulzer, and Yajun Wang.
    “Constant-Work-Space Algorithms for Shortest Paths in Trees and Simple Polygons.”
    J. Graph Algorithms Appl. 15, no. 5 (2011): 569–86.
"""

from functools import partial
from typing import Callable, Dict, Iterable, Optional, TypeVar

from geometry import Edge, Funnel, IntersectionPoint, Point, Polygon, Trapezoid
from geometry.polygon_helper import PolygonPoint

T = TypeVar('T')


def prepare_jarvis_march(polygon: Polygon, funnel: Funnel, trapezoid: Trapezoid, right_of: bool, went_left: bool,
                         boundary: Optional[Edge]=None) -> Dict:
    """Prepare data for Jarvis march.

    Args:
        polygon: A polygon.
        funnel: The current funnel.
        trapezoid: The current trapezoid we are "standing" in.
        right_of: Whether the thing (point or edge) is right of the funnel.
        went_left: Whether the current trapezoid is left of the previous one.
        boundary: (Optionally) the boundary we are looking at.

    Returns:
        A dictionary with the following values set to be used in jarvis_march:
        start_index, end_index, direction and good_turn.

    Raises:
        AssertionError: If a type check fails.
    """
    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(polygon, Polygon)
    assert isinstance(funnel, Funnel)
    assert isinstance(trapezoid, Trapezoid)
    assert isinstance(right_of, bool)
    assert isinstance(went_left, bool)
    assert boundary is None or isinstance(boundary, Edge)

    result = dict()

    if right_of:
        # If the boundary is right of our visibility we have to...
        # ... walk in counter-clockwise order ...
        result['direction'] = 1
        # ... starting at the right funnel boundary ...
        result['start_index'] = funnel.first.index
        # ... accepting vertices as "better" if they turn counter-
        # clockwise ...
        result['good_turn'] = Point.CCW_TURN
        # ... until we reach our last vertex to be checked (i.e. the one
        # on or directly before the boundary).
        if boundary is not None and boundary.a.index is not None:
            result['end_index'] = boundary.a.index
        else:
            # If the boundary point is no vertex we choose the last
            # vertex before the boundary by looking at the polygon edges
            # enclosing the trapezoid
            if went_left:
                result['end_index'] = trapezoid.top_edge_ix
            else:
                result['end_index'] = trapezoid.bot_edge_ix
    else:
        # If the boundary is left of our visibility we have to...
        # ... walk in clockwise order ...
        result['direction'] = -1
        # ... starting at the left funnel boundary ...
        result['start_index'] = funnel.second.index
        # ... accepting vertices as "better" if they turn clockwise.
        result['good_turn'] = Point.CW_TURN
        # ... until we reach our last vertex to be checked (i.e. the one
        # directly before the boundary).
        if boundary is not None and boundary.b.index is not None:
            result['end_index'] = boundary.b.index
        else:
            # If the boundary point is no vertex we choose the last
            # vertex before the boundary by looking at the polygon edges
            # enclosing the trapezoid
            if went_left:
                result['end_index'] = trapezoid.bot_edge_ix + 1
            else:
                result['end_index'] = trapezoid.top_edge_ix + 1
            # Make sure we do not run out of the vertex index domain
            result['end_index'] %= polygon.len

    return result


def jarvis_march(polygon: Polygon, start_index: int, end_index: int, direction: int, good_turn: int,
                 predicate: Callable[[Point], T], ignore: Callable[[Point, Point], bool]=lambda x: False
                 ) -> Iterable[Point]:
    """Do a Jarvis march on the given polygon.

    We start at start_index going into direction stopping at end_index. For
    every vertex we consider appropriate predicate is applied. If it yields
    something which not evaluates to False we immediately stop the march and
    return the predicate result together with the vertex and a list of all
    points visited beforehand.

    Args:
        ignore: A function which is called for every vertex and should return True iff this vertex is to be ignored
            during the jarvis march.
        polygon: A polygon.
        start_index: The index of the starting vertex.
        end_index: The index of the last vertex to consider.
        direction: The direction in which we walk along the polygon edge. Needs
            to be either 1 or -1.
        good_turn: If the current, the next and a third vertex form a turn that
            is the same as good_turn, the third will be chosen over the next.
        predicate: A function that takes a vertex as an argument and decides
            whether to continue the march or stop.

    Returns:
        A 3-tuple (result, point, visited) in which result is the result of the
        predicate function, point is the point which fulfils the predicate and
        visited is a list of vertices visited in between.

    Raises:
        AssertionError:
            a) A type check fails.
            b) None of the vertices in the specified range fulfilled
                the predicate.
    """
    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(polygon, Polygon)
    assert isinstance(start_index, int)
    assert isinstance(end_index, int)
    assert isinstance(direction, int)
    assert isinstance(good_turn, int)

    first = polygon.point(start_index)
    while True:
        point_loc.properties['predicates'] += 1
        result = predicate(first)

        # If the result does not evaluate to False return
        if result:
            return result, first

        # If this assertion fails none of the vertices fulfilled the predicate
        assert first.index != end_index

        second = polygon.point(first.index + direction)

        if second.index != end_index:
            for index in polygon.indices(second.index + direction, end_index,
                                         direction):
                point = polygon.point(index)
                point_loc.properties['ignores_theo'] += 1
                if Point.turn(first, second, point) == good_turn:
                    point_loc.properties['ignores'] += 1
                    if not ignore(first, point):
                        second = point

        yield first
        first = second


def ignore_function(points, funnel, good_position):
    """Return a function that ignores points not in the area defined by points and good_position of funnel."""
    def ignore(first, second):
        return (second.x > max(p.x for p in points) or second.x < min(p.x for p in points) or
                funnel.position_of(second) != good_position)

    return ignore


def point_loc(polygon: Polygon, s: Point, t: Point) -> Iterable[Point]:
    """Return the shortest path from s to t in the given polygon.

    This function uses only constant additional space and takes time O(n^2).

    Args:
        polygon: A polygon in counter-clockwise order.
        s: The start point (inside the polygon).
        t: The end point (inside the polygon).

    Returns:
        An iterator over the list of all vertex points of the polygonal chain
        representing the shortest geodesic path from s to t inside the polygon.

    Raises:
        AssertionError:
            a) A type check fails.
            b) The number of neighbours found on one side of a trapezoid is not
                1 or 2.
            c) The Jarvis march throws an AssertionError.
    """
    # ==========================================================================
    # Reset properties which can be accessed later on.
    # ==========================================================================
    point_loc.properties = dict(iterations=0, jarvis_marches=0, predicates=0, ignores=0, ignores_theo=0)

    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(polygon, Polygon)
    assert isinstance(s, Point)
    assert isinstance(t, Point)

    # ==========================================================================
    # Imports.
    # ==========================================================================
    from geometry import Funnel

    # ==========================================================================
    # Trivial case: s == t.
    # ==========================================================================
    # In the very trivial case the start and end point are identical thus we can
    # just return without any calculation.
    if s == t:
        yield s
        return

    # Save s and t so we can output the original values even though we modify the
    # original ones
    original_s = s
    original_t = t

    # ==========================================================================
    # Locate s and t. Trivial case: both in same trapezoid.
    # ==========================================================================
    # Locate start and end point inside our polygon.
    s_trapezoid = polygon.trapezoid(s)
    t_trapezoid = polygon.trapezoid(t)

    # If s lies directly on trapezoid boundary shift it by some small value
    if s.x in (s_trapezoid.x_left, s_trapezoid.x_right):
        shift = min(s_trapezoid.x_right - s_trapezoid.x_left, 0.00002) / 2
        if s.x == s_trapezoid.x_left:
            s = Point(s.x + shift, s.y)
        else:
            s = Point(s.x - shift, s.y)
        s_trapezoid = polygon.trapezoid(s)

    # If t lies directly on trapezoid boundary shift it by some small value
    if t.x in (t_trapezoid.x_left, t_trapezoid.x_right):
        shift = min(t_trapezoid.x_right - t_trapezoid.x_left, 0.00002) / 2
        if t.x == t_trapezoid.x_left:
            t = Point(t.x + shift, t.y)
        else:
            t = Point(t.x - shift, t.y)
        t_trapezoid = polygon.trapezoid(t)

    # If both points are located inside the same trapezoid just return both in
    # order
    if s_trapezoid == t_trapezoid:
        yield original_s
        yield original_t
        return

    # ==========================================================================
    # Preparation.
    # ==========================================================================
    # The cusp is the point we are always standing at and from which we can see
    # the trapezoid boundaries we are visiting. It gets updates in case we lose
    # visibility. We obviously start at the starting point.
    cusp = s
    # The funnel is our visibility angle.
    funnel = None
    # We also need to save the trapezoid we are currently in and the one we are
    # coming from
    current_trapezoid = s_trapezoid
    previous_trapezoid = None
    boundary = None
    previous_boundary = None

    # ==========================================================================
    # Walking the trapezoids.
    # ==========================================================================
    while current_trapezoid != t_trapezoid:
        point_loc.properties['iterations'] += 1
        # ----------------------------------------------------------------------
        # Finding the next trapezoid.
        # ----------------------------------------------------------------------

        # Find out whether we have to go left or right to find t
        go_left = t_trapezoid.is_left_of(current_trapezoid)
        # Get the neighbouring trapezoids only on the side we are looking at
        if go_left:
            neighbours = polygon.neighbour_trapezoids(current_trapezoid, 0b10)
        else:
            neighbours = polygon.neighbour_trapezoids(current_trapezoid, 0b01)

        # Each trapezoid side has at most 2 neighbours (due to not two
        # x-coordinates being the same). Furthermore if we need to go to one
        # side there has to be at least one neighbour.
        assert len(neighbours) in (1, 2)

        # Since we are going to select a new current trapezoid save it already
        previous_trapezoid = current_trapezoid

        # Choose the first neighbour if we only have one or it lies in the right
        # direction
        if (len(neighbours) == 1 or
                (go_left and t_trapezoid.is_left_of(neighbours[0])) or
                (not go_left and t_trapezoid.is_right_of(neighbours[0]))):
            current_trapezoid = neighbours[0]
        else:
            current_trapezoid = neighbours[1]

        # Get the boundary between the old and the new current trapezoid
        previous_boundary = boundary
        boundary = current_trapezoid.intersection(previous_trapezoid)
        # Edges need to be oriented in counter-clockwise direction
        if Point.turn(cusp, boundary.a, boundary.b) == Point.CW_TURN:
            boundary.reverse()
        elif Point.turn(cusp, boundary.a, boundary.b) == Point.NO_TURN:
            # Edge is always oriented from top to bottom -- so if we go right it
            # should be reversed so to have it correct
            if not go_left:
                boundary.reverse()

        # On encountering the first boundary we do not have a funnel yet. We
        # then create it and start looking for the next trapezoid
        if funnel is None:
            funnel = Funnel(cusp, boundary.a, boundary.b)
            continue

        # ----------------------------------------------------------------------
        # Checking (and possibly updating) the visibility.
        # ----------------------------------------------------------------------

        # Check where both boundary end points are in respect to the funnel
        position_of_a = funnel.position_of(boundary.a)
        position_of_b = funnel.position_of(boundary.b)

        # Save whether both end points are on the same side of the funnel
        both_right_of = position_of_a == position_of_b == Funnel.RIGHT_OF
        both_left_of = position_of_a == position_of_b == Funnel.LEFT_OF

        # ----------------------------------------------------------------------
        # CASE 1: We do not see the boundary any more.
        # ----------------------------------------------------------------------
        if both_left_of or both_right_of:
            # The current view point will definitely change now.
            # We have to take care of the special case in which the cusp is the
            # starting point, because it might have been shifted by a small bit.
            if cusp == s:
                yield original_s
            else:
                yield cusp

            # ------------------------------------------------------------------
            # Prepare the Jarvis march
            # ------------------------------------------------------------------
            point_loc.properties['jarvis_marches'] += 1
            params = prepare_jarvis_march(polygon, funnel, current_trapezoid,
                                          both_right_of, go_left, boundary)

            # ------------------------------------------------------------------
            # Actually perform the Jarvis march
            # ------------------------------------------------------------------
            if previous_boundary is None:
                x_bound_point = boundary.a
            else:
                x_bound_point = previous_boundary.a
            if both_right_of:
                ignore_func = ignore_function((cusp, x_bound_point), funnel, Funnel.RIGHT_OF)
            else:
                ignore_func = ignore_function((cusp, x_bound_point), funnel, Funnel.LEFT_OF)

            # Since polygon.point_sees_edge2 returns a tuple of the two funnel
            # points we directly extract them. Additionally we get the new cusp
            # and yield all vertices visited until finding cusp.
            (v1, v2), cusp = yield from jarvis_march(
                polygon=polygon,
                predicate=partial(polygon.point_sees_edge2, edge=boundary),
                # ignore=lambda first, second: not polygon.point_sees_other_point(first, second),
                ignore=ignore_func,
                # ignore=lambda u: u.x > max(s.x, cusp.x, boundary.a.x) or
                #                  u.x < min(s.x, cusp.x, boundary.a.x),
                **params
            )

            # ------------------------------------------------------------------
            # Update the cusp and the funnel
            # ------------------------------------------------------------------

            # In the special case in which the cusp falls together with an end
            # point of our edge we advance the funnel point on the next edge
            # into the right direction.
            # (We only compare cusp with v1 since polygon.point_sees_edge
            # guarantees to return the funnel point which falls together first.)
            if v1 == cusp:
                # If the cusp falls together with the top right or bottom left
                # edge we choose the next counter-clockwise point
                if v1.index in (current_trapezoid.top_right_ix,
                                current_trapezoid.bot_left_ix):
                    v1 = polygon.point(v1.index + 1)
                # If the cusp falls together with the top left or bottom right
                # edge we choose the next clockwise point
                elif v1.index in (current_trapezoid.bot_right_ix,
                                  current_trapezoid.top_left_ix):
                    v1 = polygon.point(v1.index - 1)

                # Since v1 and v2 will be the funnel boundary points they
                # shall be in the right (counter-clockwise) order
                if Point.turn(cusp, v1, v2) == Point.CW_TURN:
                    v1, v2 = v2, v1

            # In some cases the funnel points returned by
            # polygon.point_sees_edge are not vertices but lie on polygon edges.
            # We do not want to have those points as funnel points since they
            # can suffer from floating point inaccuracies.
            # This should only be a problem iff the point lies on an edge
            # incident to the cusp for then the other endpoint may or may not be
            # found inside the funnel.
            if isinstance(v1, IntersectionPoint) and v1.index is None and isinstance(cusp, PolygonPoint):
                if v1.edge in (cusp.index, (cusp.index - 1) % polygon.len):
                    # For v1 we can safely choose the endpoint of the edge which is
                    # "more counter-clockwise"
                    v1 = polygon.point(v1.edge + 1)
            if isinstance(v2, IntersectionPoint) and v2.index is None and isinstance(cusp, PolygonPoint):
                if v2.edge in (cusp.index, (cusp.index - 1) % polygon.len):
                    # For v2 we can safely choose the endpoint of the edge which is
                    # "more clockwise"
                    v2 = polygon.point(v2.edge)

            funnel.cusp = cusp
            funnel.first = v1
            funnel.second = v2

        # ----------------------------------------------------------------------
        # CASE 2: We see the boundary but we need to shrink the visibility.
        # ----------------------------------------------------------------------
        else:
            # If needed (i.e. if the edge reduces the funnel) update the
            # second and first funnel point
            if funnel.contains(boundary.a) and boundary.a.index is not None:
                funnel.first = boundary.a
            if funnel.contains(boundary.b) and boundary.b.index is not None:
                funnel.second = boundary.b

    # ==========================================================================
    # Do the final Jarvis march
    # ==========================================================================
    # We have to take care of the special case in which the cusp is the
    # starting point, because it might have been shifted by a small bit.
    if cusp == s:
        yield original_s
    else:
        yield cusp

    if not polygon.point_sees_other_point(cusp, t):
        # Save whether the previous polygon is left or right of the
        # current one
        go_left = previous_trapezoid.is_right_of(current_trapezoid)

        point_loc.properties['jarvis_marches'] += 1
        params = prepare_jarvis_march(polygon, funnel, current_trapezoid,
                                      funnel.position_of(t) == Funnel.RIGHT_OF,
                                      go_left)

        # ------------------------------------------------------------------
        # Actually perform the Jarvis march
        # ------------------------------------------------------------------

        if funnel.position_of(t) == Funnel.RIGHT_OF:
            ignore_func = ignore_function((cusp, boundary.a), funnel, Funnel.RIGHT_OF)
        else:
            ignore_func = ignore_function((cusp, boundary.a), funnel, Funnel.LEFT_OF)

        # Since we are nearly finished we only care about the list of visited
        # nodes and the new cusp (which is not contained in the list)
        _, cusp = yield from jarvis_march(
            polygon=polygon,
            predicate=partial(polygon.point_sees_other_point, other_point=t),
            # ignore=lambda first, second: not polygon.point_sees_other_point(first, second),
            ignore=ignore_func,
            # ignore=lambda u: u.x > max(s.x, cusp.x, t.x, boundary.a.x) or
            #                  u.x < min(s.x, cusp.x, t.x, boundary.a.x),
            **params
        )

        yield cusp

    yield original_t
