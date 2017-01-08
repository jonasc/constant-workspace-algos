"""Defines a function to load polygons from files."""
import os
import subprocess
from typing import List
from typing import Tuple

from defaults import digits, size
from . import Point, Polygon, TriangulatedPolygon


def prevent_same_x_coordinate(data: List[Tuple[float, float]], max_size: int = size, digits: int = digits
                              ) -> List[Tuple[float, float]]:
    """Prevent that two vertices have the same x-coordinate."""
    # Find out biggest (rounded) coordinate
    max_coordinate = max([max(p) for p in data])
    max_coordinate = round(max_coordinate + 0.5, 0)

    # If there are two same x-coordinates add some small value to the
    # x-coordinate (depending on the y-coordinate) and (if needed) raise the
    # precision automatically
    transform = True
    first = True
    while transform:
        transform = False

        new_data = [(round(x * max_size / max_coordinate, digits),
                     round(y * max_size / max_coordinate, digits))
                    for (x, y) in data]

        x_values = [x for (x, y) in new_data]
        x_values.sort()

        smallest = max_size
        for ix in range(len(x_values) - 1):
            if x_values[ix] == x_values[ix + 1]:
                transform = True
            elif abs(x_values[ix] - x_values[ix + 1]) < smallest:
                smallest = abs(x_values[ix] - x_values[ix + 1])

        if transform:
            factor = smallest / (2 * max_size)
            new_data = [(x + y * factor, y) for (x, y) in data]
            if first:
                first = False
            else:
                digits += 1

    return new_data


def load_polygon(filename: str, index: int = None, max_size: int = size, digits: int = digits,
                 no_transform: bool = False) -> Polygon:
    """Load a polygon from a file.

    If an index is given a file with multiple polygons is assumed and the one on
    the correct line (starting at 1) is loaded. Otherwise it is assumed that the
    file only contains one polygon and we treat it differently.

    Args:
        filename: A path to file which contains one or more polygons.
        index: If given it indicates which of the multiple polygons to load.
        max_size: The maximum width / height of the polygon.
            The polygon is normalized with this number.
        digits: The number of decimal digits which should be retained from the
            vertex-coordinates.

    Returns:
        A new polygon.
    """
    data = []
    with open(filename, 'r') as f:
        if isinstance(index, int):
            # If we have an index given we have to choose the right line
            for line in f:
                if index == 1:
                    # The line consists of "x y" coordinates delimited by ':'
                    for pair in line.strip().split(':'):
                        data.append(pair.strip().split(' '))
                    index = 0
                    break
                index -= 1
            if index >= 1:
                raise IndexError(
                    'file "{file}" does not contain polygon with index {index}.'.format(file=filename, index=index))
        else:
            # If there is no index given read a coordinate pair from every line
            for line in f:
                if line.startswith('%'):
                    break
                data.append(line.strip().split(' '))

    if not data:
        raise ValueError('No data read from file.')

    # Convert everything to floats
    data = [(float(x), float(y)) for [x, y] in data]

    if no_transform:
        new_data = data
    else:
        new_data = prevent_same_x_coordinate(data)

    # Return new polygon, normalize every point with respect to max_size
    return Polygon([Point(x, y) for (x, y) in new_data])


def create_random_polygons(vertices, number, bounding_box, digits, triangulated=False):
    """Create random polygons using java program."""
    dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'polygons-swp')

    # Run polygon creator
    process = subprocess.run(
        ['./run.sh', '--boundingbox', str(bounding_box), '--number', str(number), '--points', str(vertices),
         '--no-statistics', '--no-header'],
        cwd=dir, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE,
        universal_newlines=True
    )

    # Extract each polygon from its output line
    polygons = []
    for line in process.stdout.strip().split('\n'):
        points = [Point(round(float(x), digits), round(float(y), digits)) for x, y in
                  [point.split(' ') for point in line.split(':')]]
        if triangulated:
            polygons.append(TriangulatedPolygon(points))
        else:
            polygons.append(Polygon(points))

    return polygons
