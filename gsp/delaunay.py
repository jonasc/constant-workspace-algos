"""Calculate the geodesic shortest path in a polygon.

Asano, Tetsuo, Wolfgang Mulzer, and Yajun Wang.
    “Constant-Work-Space Algorithms for Shortest Paths in Trees and Simple Polygons.”
    J. Graph Algorithms Appl. 15, no. 5 (2011): 569–86.
"""
from functools import partial
from typing import Callable, Dict, Iterable, Tuple, TypeVar

from geometry import Edge
from geometry.delaunay_triangle import DelaunayTriangle
from geometry.funnel import Funnel
from geometry.point import Point
from geometry.polygon import Polygon

T = TypeVar('T')


def prepare_jarvis_march(polygon: Polygon, funnel: Funnel, triangle: DelaunayTriangle, right_of: bool,
                         boundary: Edge) -> Dict:
    """Prepare data for Jarvis march.

    Args:
        polygon: A polygon.
        funnel: The current funnel.
        triangle: The current triangle we are "standing" in.
        right_of: Whether the thing (point or edge) is right of the funnel.
        boundary: The boundary we are looking at.

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
    assert isinstance(triangle, DelaunayTriangle)
    assert isinstance(right_of, bool)
    assert isinstance(boundary, Edge)

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
        # ... until we reach our last vertex to be checked.

        # Here we need to do some "magic" to get the right last vertex.
        # We look at the given boundary and the "node distance" to the start point. The one nearer is the end index.
        if (
                (boundary.a.index - result['start_index']) % polygon.len <
                (boundary.b.index - result['start_index']) % polygon.len):
            result['end_index'] = boundary.a.index
        else:
            result['end_index'] = boundary.b.index
    else:
        # If the boundary is left of our visibility we have to...
        # ... walk in clockwise order ...
        result['direction'] = -1
        # ... starting at the left funnel boundary ...
        result['start_index'] = funnel.second.index
        # ... accepting vertices as "better" if they turn clockwise.
        result['good_turn'] = Point.CW_TURN
        # ... until we reach our last vertex to be checked.

        # Here we need to do some "magic" to get the right last vertex.
        # We look at the given boundary and the "node distance" to the start point. The one nearer is the end index.
        if (
                (result['start_index'] - boundary.a.index) % polygon.len <
                (result['start_index'] - boundary.b.index) % polygon.len):
            result['end_index'] = boundary.a.index
        else:
            result['end_index'] = boundary.b.index

    return result


def jarvis_march(polygon: Polygon, start_index: int, end_index: int, direction: int, good_turn: int,
                 predicate: Callable[[Point], T], ignore: Callable[[Point], bool]=lambda x: False
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
        shortest_path.properties['predicates'] += 1
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
                shortest_path.properties['ignores_theo'] += 1
                if Point.turn(first, second, point) == good_turn:
                    shortest_path.properties['ignores'] += 1
                    if not ignore(point):
                        second = polygon.point(index)

        yield first
        first = second


def subtree_search(polygon: Polygon, u: DelaunayTriangle, v: DelaunayTriangle, t: DelaunayTriangle) -> bool:
    """Check whether the subtree of u rooted at v contains t."""
    current_triangle = u
    neighbor = v
    while current_triangle != t and (current_triangle != v or neighbor != u):
        next_node = polygon.delaunay_next_neighbour(neighbor, current_triangle)
        current_triangle = neighbor
        neighbor = next_node
    return current_triangle == t


def linear_time_find_feasible_subtree(polygon: Polygon, u: DelaunayTriangle, v: DelaunayTriangle, s: DelaunayTriangle,
                                      t: DelaunayTriangle = None) -> DelaunayTriangle:
    """Return a child of u whose subtree contains t. Starts at v."""
    for edge in u.edges_from(u.common_edge(v)):
        w = polygon._complete_other_delaunay_triangle_of_edge(edge, u)
        if subtree_search(polygon, u, w, t):
            return w


def adv_search(polygon: Polygon, u: DelaunayTriangle, v: DelaunayTriangle, u_: DelaunayTriangle, v_: DelaunayTriangle,
               t: DelaunayTriangle) -> Tuple[bool, bool, DelaunayTriangle, DelaunayTriangle]:
    """Advance the Eulerian tour in the subtree rooted at v."""
    v__ = polygon.delaunay_next_neighbour(v_, u_)
    u__ = v_

    if u__ == v and v__ == u:
        return (False, False, u__, v__)

    if v__ == t:
        return (True, False, u__, v__)

    return (False, True, u__, v__)


def parallel_find_feasible_subtree(polygon: Polygon, u: DelaunayTriangle, v: DelaunayTriangle, s: DelaunayTriangle,
                                   t: DelaunayTriangle) -> DelaunayTriangle:
    """Return a child of u whose subtree contains t. Starts at v."""
    f_neighbor = v
    s_neighbor = polygon.delaunay_next_neighbour(u, v)
    last_neighbor = s_neighbor
    num_of_neighbors = polygon.delaunay_neighbour_number(u) - int(u != s)

    # NOTE: The second condition is an addition to the pseudo code because
    # otherwise the code won't terminate in all cases
    if num_of_neighbors == 1 or f_neighbor == t:
        return f_neighbor
    # NOTE: This check is an addition to the pseudo code because otherwise the
    # code won't terminate in all cases
    elif s_neighbor == t:
        return s_neighbor

    one = u
    one_next = f_neighbor
    two = u
    two_next = s_neighbor

    while True:
        (sigf1, sigc1, one, one_next) = adv_search(
            polygon, u, f_neighbor, one, one_next, t
        )
        (sigf2, sigc2, two, two_next) = adv_search(
            polygon, u, s_neighbor, two, two_next, t
        )

        if sigf1:
            return f_neighbor
        if sigf2:
            return s_neighbor

        if not sigc1:
            f_neighbor = polygon.delaunay_next_neighbour(u, last_neighbor)
            one_next = f_neighbor
            last_neighbor = f_neighbor
            one = u
            num_of_neighbors -= 1

            if num_of_neighbors == 1:
                return s_neighbor
            # NOTE: This check is an addition to the pseudo code because
            # otherwise the code won't find the shortest path
            if f_neighbor == t:
                return f_neighbor
        if not sigc2:
            s_neighbor = polygon.delaunay_next_neighbour(u, last_neighbor)
            two_next = s_neighbor
            last_neighbor = s_neighbor
            two = u
            num_of_neighbors -= 1

            if num_of_neighbors == 1:
                return f_neighbor
            # NOTE: This check is an addition to the pseudo code because
            # otherwise the code won't find the shortest path
            if s_neighbor == t:
                return s_neighbor


def ignore_function(boundary, funnel, good_position):
    """Return a function that ignores points not in the area defined by points and good_position of funnel."""
    def ignore(point):
        return (Point.turn(boundary.a, boundary.b, point) == Point.CW_TURN or
                funnel.position_of(point) != good_position)

    return ignore


def shortest_path(polygon: Polygon, s: Point, t: Point) -> Iterable[Point]:
    """Find the shortest path from s to t inside polygon."""
    # ==========================================================================
    # Reset properties which can be accessed later on.
    # ==========================================================================
    shortest_path.properties = dict(iterations=0, jarvis_marches=0, predicates=0, ignores=0, ignores_theo=0)

    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(polygon, Polygon)
    assert isinstance(s, Point)
    assert isinstance(t, Point)

    # ==========================================================================
    # Trivial case: s == t.
    # ==========================================================================
    # In the very trivial case the start and end point are identical thus we can
    # just return without any calculation.
    if s == t:
        yield s
        return

    # ==========================================================================
    # Locate s and t. Trivial case: both in same triangle.
    # ==========================================================================
    # Locate start and end point inside our polygon.
    s_triangle = polygon.locate_point_in_triangle(s)
    t_triangle = polygon.locate_point_in_triangle(t)

    # If any point is not inside the polygon return
    if s_triangle is None or t_triangle is None:
        return

    # If both points are located inside the same triangle just return both in order
    if s_triangle == t_triangle:
        yield s
        yield t
        return

    # ==========================================================================
    # Preparation.
    # ==========================================================================
    # The cusp is the point we are always standing at and from which we can see the triangle boundaries we are visiting.
    # It gets updated in case we lose visibility. We obviously start at the starting point.
    cusp = s
    # The funnel is our visibility angle.
    funnel = None
    # We also need to save the trapezoid we are currently in.
    current_triangle = s_triangle
    previous_triangle = current_triangle
    boundary = None

    # We choose the first neighbour to look at
    start_neighbour = polygon.delaunay_first_neighbour(current_triangle)

    # ==========================================================================
    # Walking the triangles.
    # ==========================================================================
    while current_triangle != t_triangle:
        shortest_path.properties['iterations'] += 1

        previous_triangle = current_triangle
        current_triangle = parallel_find_feasible_subtree(polygon, previous_triangle, start_neighbour, s_triangle,
                                                          t_triangle)

        previous_boundary = boundary
        # Get the boundary between the old and the new current triangle
        boundary = current_triangle.common_edge(previous_triangle)
        # Edges need to be oriented in counter-clockwise direction
        if Point.turn(cusp, boundary.a, boundary.b) == Point.CW_TURN:
            boundary.reverse()
        elif Point.turn(cusp, boundary.a, boundary.b) == Point.NO_TURN:
            # FIXME: We should do something if edge is aligned with cusp
            # Idea: Look at boundary from third point of previous triangle
            previous_triangle_points = list(previous_triangle.points)
            previous_triangle_points.remove(boundary.a)
            previous_triangle_points.remove(boundary.b)
            assert len(previous_triangle_points) == 1
            previous_triangle_point = previous_triangle_points[0]
            if Point.turn(previous_triangle_point, boundary.a, boundary.b) == Point.CW_TURN:
                boundary.reverse()

        # On encountering the first boundary we do not have a funnel yet. We
        # then create it and start looking for the next trapezoid
        if funnel is None:
            funnel = Funnel(cusp, boundary.a, boundary.b)

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
            # The current view point will definitely change now
            yield cusp

            # ------------------------------------------------------------------
            # Prepare the Jarvis march
            # ------------------------------------------------------------------
            shortest_path.properties['jarvis_marches'] += 1
            params = prepare_jarvis_march(polygon, funnel, current_triangle,
                                          both_right_of, boundary)

            # ------------------------------------------------------------------
            # Actually perform the Jarvis march
            # ------------------------------------------------------------------
            if both_right_of:
                ignore_func = ignore_function(previous_boundary or boundary, funnel, Funnel.RIGHT_OF)
            else:
                ignore_func = ignore_function(previous_boundary or boundary, funnel, Funnel.LEFT_OF)

            # Since polygon.point_sees_edge2 returns a tuple of the two funnel
            # points we directly extract them. Additionally we get the new cusp
            # and yield all vertices visited until finding cusp.
            (v1, v2), cusp = yield from jarvis_march(
                polygon=polygon,
                predicate=partial(polygon.point_sees_edge2, edge=boundary),
                ignore=ignore_func,
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
                triangle_points = current_triangle.points
                assert v1 in triangle_points
                assert v2 in triangle_points

                # Going in clockwise direction
                if params['direction'] == 1:
                    v1 = polygon.point(cusp.index + 1)
                else:
                    v1 = polygon.point(cusp.index - 1)
                    # We need to swap v1 and v2 to have them in the right order
                    v1, v2 = v2, v1

            funnel.cusp = cusp
            funnel.first = v1
            funnel.second = v2

        # ----------------------------------------------------------------------
        # CASE 2: We see the boundary but we need to shrink the visibility.
        # ----------------------------------------------------------------------
        else:
            # If needed (i.e. if the edge reduces the funnel) update the
            # second and first funnel point
            if position_of_a == Funnel.INSIDE:
                funnel.first = boundary.a
            if position_of_b == Funnel.INSIDE:
                funnel.second = boundary.b

        start_neighbour = polygon.delaunay_next_neighbour(current_triangle, previous_triangle)

    # ==========================================================================
    # Do the final Jarvis march
    # ==========================================================================
    yield cusp

    if not polygon.point_sees_other_point(cusp, t):
        shortest_path.properties['jarvis_marches'] += 1
        params = prepare_jarvis_march(polygon, funnel, current_triangle, funnel.position_of(t) == Funnel.RIGHT_OF,
                                      current_triangle.common_edge(previous_triangle))

        # ------------------------------------------------------------------
        # Actually perform the Jarvis march
        # ------------------------------------------------------------------

        # Since we are nearly finished we only care about the list of visited
        # nodes and the new cusp (which is not contained in the list)
        _, cusp = yield from jarvis_march(
            polygon=polygon,
            predicate=partial(polygon.point_sees_other_point, other_point=t),
            ignore=ignore_function(boundary, funnel, funnel.position_of(t)),
            **params
        )

        yield cusp

    yield t
