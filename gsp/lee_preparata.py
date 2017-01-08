"""Calculate the geodesic shortest path in a polygon with linear space.

Lee, D. T., and F. P. Preparata.
    “Euclidean Shortest Paths in the Presence of Rectilinear Barriers.”
    Networks 14, no. 3 (1984): 393–410. doi:10.1002/net.3230140304.
"""
from collections import deque
from typing import Iterable, List

from geometry import Edge, Point, TriangulatedPolygon, TriangulatedPolygonTriangle


def shortest_path_as_diagonals(polygon: TriangulatedPolygon, s_triangle: TriangulatedPolygonTriangle,
                               t_triangle: TriangulatedPolygonTriangle) -> List[Edge]:
    """O(n): Return all diagonals the shortest path crosses from s_triangle to t_triangle."""
    def recurse(triangle: TriangulatedPolygonTriangle, predecessor: TriangulatedPolygonTriangle = None
                ) -> List[Edge]:
        """
        Return a list of diagonals (last one first) from triangle to t_triangle ignoring predecessor.

        The diagonals are the dual edges of all the edges we need to visit in the tree towards t_triangle.
        """
        # Loop trough all the neighbours
        for neighbour_index in triangle.neighbour_indices:
            neighbour = polygon.triangles[neighbour_index]
            if neighbour == t_triangle:
                # We reached the goal t_triangle
                return [triangle.common_edge(neighbour)]
            if neighbour != predecessor:
                try:
                    # Try to look for t_triangle recursively. If t_triangle cannot be found an exception is thrown.
                    result = recurse(neighbour, triangle)
                except ValueError:
                    pass
                else:
                    # No exception thrown => t_triangle was found.
                    result.append(triangle.common_edge(neighbour))
                    return result

        raise ValueError()

    diagonals = recurse(s_triangle)
    diagonals.reverse()
    return diagonals


def shortest_path_as_diagonals2(polygon: TriangulatedPolygon, s_triangle: TriangulatedPolygonTriangle,
                                t_triangle: TriangulatedPolygonTriangle) -> List[Edge]:
    """O(n): Return all diagonals the shortest path crosses from s_triangle to t_triangle."""
    s_index = polygon.triangles.index(s_triangle)
    seen_triangles = {s_index}
    dfs_stack = [s_triangle]
    edges = []
    while dfs_stack[-1] != t_triangle:
        current = dfs_stack[-1]
        for neighbor_index in current.neighbour_indices:
            neighbor = polygon.triangles[neighbor_index]
            if neighbor_index in seen_triangles:
                continue
            dfs_stack.append(neighbor)
            edges.append(current.common_edge(neighbor))
            seen_triangles.add(neighbor_index)
            break
        else:
            # All neighbors were already visited
            dfs_stack.pop()
            edges.pop()

    return edges


def shortest_path(polygon: TriangulatedPolygon, s: Point, t: Point) -> Iterable[Point]:
    """Find the shortest path from s to t inside polygon."""
    # ==========================================================================
    # Reset properties which can be accessed later on.
    # ==========================================================================
    shortest_path.properties = dict(iterations=0)

    # ==========================================================================
    # Type checking.
    # ==========================================================================
    assert isinstance(polygon, TriangulatedPolygon)
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
    # Find the shortest path in the dual tree.
    # ==========================================================================
    diagonals = shortest_path_as_diagonals(polygon, s_triangle, t_triangle)
    # Append one final edge from one end-point of the last diagonal to t. This is needed to make sure we ultimately
    # visit t.
    diagonals.append(Edge(diagonals[-1].a, t))

    # ==========================================================================
    # Preparation.
    # ==========================================================================
    cusp = s
    funnel = deque([diagonals[0].a, cusp, diagonals[0].b])

    if Point.turn(s, diagonals[0].a, diagonals[0].b) == Point.CCW_TURN:
        funnel.reverse()

    # ==========================================================================
    # Walking the triangles.
    # ==========================================================================
    for diagonal in diagonals[1:]:
        shortest_path.properties['iterations'] += 1
        # Save the new points as left and right
        left = diagonal.a
        right = diagonal.b

        # We know, that every new diagonal has exactly one end point common with the current funnel. We check whether
        # the common vertex is the "wrong" one and in this case swap the diagonal's "left" and "right".
        if funnel[0] == right or funnel[-1] == left:
            left, right = right, left

        if left == funnel[0]:
            # As long as the new point does not extend the existing funnel in a concave fashion we remove the last
            # funnel vertex. We also stop when reaching the cusp since we need to think differently after reaching it.
            while funnel[-1] != cusp and Point.turn(funnel[-2], funnel[-1], right) == Point.CCW_TURN:
                funnel.pop()
            if funnel[-1] == cusp:
                # If we removed all funnel vertices of one side we might find the need to remove the cusp and maybe some
                # more vertices from the other side. In the end the first not removed funnel vertex is the new cusp.
                while len(funnel) > 1 and Point.turn(funnel[-1], funnel[-2], right) == Point.CCW_TURN:
                    yield funnel.pop()
                cusp = funnel[-1]
            # Our new vertex definitely extends the (new) funnel.
            funnel.append(right)
        else:
            # This is exactly analogous to the left case.
            while funnel[0] != cusp and Point.turn(funnel[1], funnel[0], left) == Point.CW_TURN:
                funnel.popleft()
            if funnel[0] == cusp:
                while len(funnel) > 1 and Point.turn(funnel[0], funnel[1], left) == Point.CW_TURN:
                    yield funnel.popleft()
                cusp = funnel[0]

            funnel.appendleft(left)

    # If either end of the funnel is our final point t we remove the other side until the cusp and then yield all points
    # belonging to the cusp because we need to visit all of them on our way to t.
    if funnel[0] == t:
        while funnel[-1] != cusp:
            funnel.pop()
        while funnel:
            yield funnel.pop()
    elif funnel[-1] == t:
        while funnel[0] != cusp:
            funnel.popleft()
        while funnel:
            yield funnel.popleft()
    else:
        yield cusp
        yield t
