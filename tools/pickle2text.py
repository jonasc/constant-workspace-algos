#!/usr/bin/env python3.5
"""Converts a pickled polygon to a text file poylgon."""
import glob
import os.path
import pickle
import sys

from geometry import Point, Polygon


def print_usage_and_exit(status=1):
    """Show help message only."""
    print('Usage: {0} [--points | -p] file1 [file2 [...]]'.format(os.path.basename(sys.argv[0])))
    sys.exit(status)


def convert_file(file, add_points):
    """Convert one file from pickle to text file."""
    with open(file, 'rb') as f:
        polygon = pickle.load(f)
        assert isinstance(polygon, Polygon)

    base_file = os.path.splitext(file)[0]

    with open('{0}.polytest'.format(base_file), 'w') as f:
        for point in polygon.points:
            assert isinstance(point, Point)
            print('{0:.4f} {1:.4f}'.format(point.x, point.y), file=f)

        if add_points:
            print('%' * 20, file=f)

            image_files = glob.glob('{0}:*->*.png'.format(base_file))
            for image_file in image_files:
                s, t = os.path.basename(image_file).split(':')[-1].split('.')[0].split('->')
                print('{0}->{1}'.format(s, t), file=f)


def convert_files(files, add_points=False):
    """Convert multiple files from pickle to text file."""
    for file in files:
        try:
            convert_file(file, add_points)
        except FileNotFoundError as e:
            print(e)


if __name__ == '__main__':
    if (len(sys.argv) == 1) or (len(sys.argv) == 2 and sys.argv[1] == '--points'):
        print_usage_and_exit()

    if sys.argv[1] in ('--points', '-p'):
        convert_files(sys.argv[2:], True)
    else:
        convert_files(sys.argv[1:], False)
