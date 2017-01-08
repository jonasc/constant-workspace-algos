"""Calculate the geodesic shortest path in a polygon.

Asano, Tetsuo, Wolfgang Mulzer, Günter Rote, and Yajun Wang.
    “Constant-Work-Space Algorithms for Geometric Problems.”
    Journal of Computational Geometry 2, no. 1 (2011): 46–68.
"""
from typing import Iterable, NamedTuple, Optional, Union

from geometry import EdgePoint, Point, Polygon, PolygonPoint, Trapezoid
from geometry.ray import Ray

MakeStepResult = NamedTuple('MakeStepResult',
                            [('old_cusp', Optional[Point]), ('cusp', PolygonPoint), ('right', Point), ('left', Point)])


def hit_polygon_boundary(p: Union[PolygonPoint, EdgePoint], q: Point, polygon: Polygon) -> EdgePoint:
    """O(n): Return the index of the edge we hit when shooting from p to q."""
    assert isinstance(p, (PolygonPoint, EdgePoint))
    assert isinstance(q, Point)
    assert isinstance(polygon, Polygon)

    # We save some edge indices which are ignored when testing edge intersections.
    # This is to take rounding errors into account.
    # The forbidden indices are either both edges left and right of the starting point (which in this case is a vertex)
    # or the edge index. If a starting point has a "None" index we get (None, ) but this is ok for us.
    forbidden_indices = (p.index, )
    if isinstance(p, PolygonPoint) and p.index is not None:
        forbidden_indices = (p.index, polygon.prev(p.index))

    # We now construct a ray from p through q and check for intersection with every polygon edge.
    # We take the intersection point with the shortest distance to p since this is the only points which can be seen
    # from p.
    ray = Ray(p, q)
    hit_point = None
    distance = None
    for ix in polygon.indices():
        edge = polygon.edge(ix)
        if ix not in forbidden_indices and ray.properly_intersects(edge):
            tmp_hit = ray.intersection_point(edge)
            tmp_distance = p.squared_distance_to(tmp_hit)
            if distance is None or tmp_distance < distance:
                hit_point = EdgePoint(tmp_hit, edge.a.index)
                distance = tmp_distance

    # TODO: Remember what exactly this was for.
    if hit_point is None:
        hit_point = q

    return hit_point


def trapezoid_subpolygon_position(polygon: Polygon, ix1: int, ix2: int, trapezoid: Trapezoid) -> int:
    """O(1): Return inside which subpolygon of `polygon` divided by `ix1` and `ix2` `trapezoid` is situated.

    Returns 1 if the trapezoid lies in the right part -1 if it lies in the left part or 0 if it crosses the boundary.
    """
    assert isinstance(trapezoid, Trapezoid)
    assert isinstance(polygon, Polygon)
    assert isinstance(ix1, int) and 0 <= ix1 < len(polygon)
    assert isinstance(ix2, int) and 0 <= ix2 < len(polygon)

    # We need to distinguish the following cases:
    # ix1 < ix2: trapezoid top and bottom edges should lie between ix1 and ix2.
    if ix1 < ix2:
        # Since the edges follow the vertices in ccw order the following are allowed edges for the trapezoid:
        # {ix1, ix1+1, ..., ix2-1}.
        if ix1 <= trapezoid.bot_edge_ix < ix2 and ix1 <= trapezoid.top_edge_ix < ix2:
            return 1
        # If the trapezoid edges are both in the following set the trapezoid lies to the left:
        # {0, 1, ..., ix1-1} u {ix2, ..., n-1}.
        if ((trapezoid.bot_edge_ix < ix1 or trapezoid.bot_edge_ix >= ix2) and (
                trapezoid.top_edge_ix < ix1 or trapezoid.top_edge_ix >= ix2)):
            return -1
        # Now either side of (ix1,ix2) has one trapezoid edge. We cannot decide.
        return 0

    # ix1 > ix2: the edges should be smaller than ix2 or bigger than ix1.
    elif ix1 > ix2:
        # Since the edges follow the vertices in ccw order the following are allowed edges for the trapezoid:
        # {0, 1, ..., ix2-1} u {ix1, ..., n-1}.
        if ((trapezoid.bot_edge_ix < ix2 or trapezoid.bot_edge_ix >= ix1) and (
                trapezoid.top_edge_ix < ix2 or trapezoid.top_edge_ix >= ix1)):
            return 1
        # If the trapezoid edges are both in the following set the trapezoid lies to the left:
        # {ix2, ix2+1, ..., ix1-1}.
        if ix2 <= trapezoid.bot_edge_ix < ix1 and ix2 <= trapezoid.top_edge_ix < ix1:
            return -1
        # Now either side of (ix1,ix2) has one trapezoid edge. We cannot decide.
        return 0

    # ix1 == ix2: this should not happen.
    else:
        assert False


def in_subpolygon(polygon: Polygon, q1: Point, q2: Point, t: Point, t_trapezoid: Trapezoid) -> bool:
    """O(1): Return whether `t` lies inside the subpolygon of `polygon` to the right of `q1`,`q2`."""
    assert isinstance(q1, (PolygonPoint, EdgePoint))
    assert isinstance(q2, (PolygonPoint, EdgePoint))
    assert isinstance(t, Point)
    assert isinstance(t_trapezoid, Trapezoid)
    assert isinstance(polygon, Polygon)

    # Because our line (q1,q2) can start and/or end on edges we need to be careful in taking decisions.

    # Find the vertex indices for q1,q2. If q1 lies on an edge we need to increase the index by one to have the smaller
    # subpolygon.
    ix1 = q1.index
    if isinstance(q1, EdgePoint):
        ix1 = polygon.next(ix1)
    # The second index does not need special treatment since the index already shrinks the polygon.
    ix2 = q2.index

    if ix1 == ix2:
        assert isinstance(q1, EdgePoint)
        return Point.turn(q1, q2, t) != Point.CCW_TURN

    # First we check in which part of the (possibly) smaller subpolygon our trapezoid lies.
    small_polygon_position = trapezoid_subpolygon_position(polygon, ix1, ix2, t_trapezoid)

    # If the trapezoid lies right to the line it is safe.
    if small_polygon_position == 1:
        return True
    # In the other cases we should have a closer look.

    # Now we widen the subpolygon s.t. we can check whether t lies completely outside our range.
    if isinstance(q1, EdgePoint):
        ix1 = polygon.prev(ix1)
    if isinstance(q2, EdgePoint):
        ix2 = polygon.next(ix2)

    # If the point does not lie inside this bigger subpolygon we can safely say it does not lie in the actual
    # subpolygon
    if ix1 != ix2:
        big_polygon_position = trapezoid_subpolygon_position(polygon, ix1, ix2, t_trapezoid)
        if big_polygon_position == small_polygon_position == -1:
            return False

    # Now the trapezoid lies somewhere between the small and the big subpolygon.
    # First we can decide with respect to the x-coordinates -- just checking where t lies with respect to line(q1,q2)
    # does not work!
    if t.is_right_of(q1) and t.is_right_of(q2):
        if (
                (isinstance(q1, EdgePoint) and q1.index == t_trapezoid.bot_edge_ix) or
                (isinstance(q2, EdgePoint) and q2.index == t_trapezoid.top_edge_ix)):
            return True
        if (
                (isinstance(q1, EdgePoint) and q1.index == t_trapezoid.top_edge_ix) or
                (isinstance(q2, EdgePoint) and q2.index == t_trapezoid.bot_edge_ix)):
            return False
    if t.left_of(q1) and t.left_of(q2):
        if (
                (isinstance(q1, EdgePoint) and q1.index == t_trapezoid.top_edge_ix) or
                (isinstance(q2, EdgePoint) and q2.index == t_trapezoid.bot_edge_ix)):
            return True
        if (
                (isinstance(q1, EdgePoint) and q1.index == t_trapezoid.bot_edge_ix) or
                (isinstance(q2, EdgePoint) and q2.index == t_trapezoid.top_edge_ix)):
            return False

    return Point.turn(q1, q2, t) != Point.CCW_TURN


def make_step(p: PolygonPoint, q1: Point, q2: Point, t: Point, polygon: Polygon, t_trapezoid: Trapezoid
              ) -> MakeStepResult:
    """O(n): Advance the given triple (p, q1, q2) towards t.

    Args:
        p:
        q1:
        q2:
        t:
        polygon:

    Returns:
    """
    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(p, PolygonPoint)
    assert isinstance(q1, (PolygonPoint, EdgePoint))
    assert isinstance(q2, (PolygonPoint, EdgePoint))
    assert isinstance(t, Point)
    assert isinstance(t_trapezoid, Trapezoid)
    assert isinstance(polygon, Polygon)

    if isinstance(q1, PolygonPoint) and Point.turn(p, q1, polygon.succ(q1)) == Point.CW_TURN:
        q_prime = hit_polygon_boundary(p, q1, polygon)
        if in_subpolygon(polygon, q1, q_prime, t, t_trapezoid):
            return MakeStepResult(old_cusp=p, cusp=q1, right=polygon.succ(q1), left=q_prime)
        else:
            return MakeStepResult(old_cusp=None, cusp=p, right=q_prime, left=q2)

    elif isinstance(q2, PolygonPoint) and Point.turn(p, q2, polygon.pred(q2)) == Point.CCW_TURN:
        q_prime = hit_polygon_boundary(p, q2, polygon)
        if in_subpolygon(polygon, q_prime, q2, t, t_trapezoid):
            return MakeStepResult(old_cusp=p, cusp=q2, right=q_prime, left=polygon.pred(q2))
        else:
            return MakeStepResult(old_cusp=None, cusp=p, right=q1, left=q_prime)

    else:
        succ_q1 = polygon.succ(q1)
        if Point.turn(p, q1, succ_q1) != Point.CW_TURN and Point.turn(p, q2, succ_q1) != Point.CCW_TURN:
            # succ(q1) lies in wedge q1,p,q2
            q_prime = hit_polygon_boundary(p, succ_q1, polygon)
            if q_prime != q2:
                if p.squared_distance_to(q_prime) >= p.squared_distance_to(succ_q1):
                    q_prime = succ_q1
                if p.index is None:
                    p_ = hit_polygon_boundary(q_prime, p, polygon)
                else:
                    p_ = p
                if in_subpolygon(polygon, p_, q_prime, t, t_trapezoid):
                    return MakeStepResult(old_cusp=None, cusp=p, right=q1, left=q_prime)
                else:
                    return MakeStepResult(old_cusp=None, cusp=p, right=q_prime, left=q2)

        pred_q2 = polygon.pred(q2)
        q_prime = hit_polygon_boundary(p, pred_q2, polygon)
        if p.squared_distance_to(q_prime) >= p.squared_distance_to(pred_q2):
            q_prime = pred_q2
        if p.index is None:
            p_ = hit_polygon_boundary(q_prime, p, polygon)
        else:
            p_ = p
        if in_subpolygon(polygon, q_prime, p_, t, t_trapezoid):
            return MakeStepResult(old_cusp=None, cusp=p, right=q_prime, left=q2)
        else:
            return MakeStepResult(old_cusp=None, cusp=p, right=q1, left=q_prime)


def shortest_path(polygon: Polygon, s: Point, t: Point) -> Iterable[Point]:
    """O(n^2): Return the shortest path from s to t in the given polygon.

    This function uses only constant additional space and takes time O(n^2).

    Args:
        polygon: A polygon in counter-clockwise order.
        s: The start point (inside the polygon).
        t: The end point (inside the polygon).

    Returns:
        An iterator over the list of all vertex points of the polygonal chain
        representing the shortest geodesic path from s to t inside the polygon.

    Raises:
        AssertionError: A type check fails.
    """
    # ==========================================================================
    # Reset properties which can be accessed later on.
    # ==========================================================================
    shortest_path.properties = dict(iterations=0)

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
    # Find next trapezoid when going from s to t. This is needed for
    # initialisation.
    # ==========================================================================

    # Find out whether we have to go left or right to find t
    go_left = t_trapezoid.is_left_of(s_trapezoid)
    # Get the neighbouring trapezoids only on the side we are looking at
    if go_left:
        neighbours = polygon.neighbour_trapezoids(s_trapezoid, 0b10)
    else:
        neighbours = polygon.neighbour_trapezoids(s_trapezoid, 0b01)

    # Each trapezoid side has at most 2 neighbours (due to not two
    # x-coordinates being the same). Furthermore if we need to go to one
    # side there has to be at least one neighbour.
    assert len(neighbours) in (1, 2)

    # Choose the first neighbour if we only have one or it lies in the right
    # direction
    if (len(neighbours) == 1 or
            (go_left and t_trapezoid.is_left_of(neighbours[0])) or
            (not go_left and t_trapezoid.is_right_of(neighbours[0]))):
        next_trapezoid = neighbours[0]
    else:
        next_trapezoid = neighbours[1]

    # Get the boundary between the old and the new current trapezoid
    boundary = next_trapezoid.intersection(s_trapezoid)
    # Edges need to be oriented in counter-clockwise direction
    if Point.turn(original_s, boundary.a, boundary.b) == Point.CW_TURN:
        boundary.reverse()
    elif Point.turn(original_s, boundary.a, boundary.b) == Point.NO_TURN:
        # Edge is always oriented from top to bottom -- so if we go right it
        # should be reversed so to have it correct
        if not go_left:
            boundary.reverse()

    # We can now define our triple (p, q1, q2) as in the algorithm
    p = PolygonPoint(original_s)

    q1 = boundary.a
    if q1.edge is not None:
        q1 = EdgePoint(q1, q1.edge)
    else:
        q1 = PolygonPoint(q1, q1.index)

    q2 = boundary.b
    if q2.edge is not None:
        q2 = EdgePoint(q2, q2.edge)
    else:
        q2 = PolygonPoint(q2, q2.index)

    # ==========================================================================
    # Call make_step until we can see t.
    # ==========================================================================
    while not polygon.point_sees_other_point(p, original_t):
        shortest_path.properties['iterations'] += 1
        point, p, q1, q2 = make_step(p, q1, q2, original_t, polygon, t_trapezoid)
        if point:
            if point.tuple() == original_s.tuple():
                yield original_s
            else:
                yield point

    # ==========================================================================
    # Finish
    # ==========================================================================
    if p.tuple() == original_s.tuple():
        yield original_s
    else:
        yield p
    yield original_t
