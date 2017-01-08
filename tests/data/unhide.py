#!/usr/bin/env python3.5
"""Remove the specified files from the 'polytest' file."""

import sys

from os import path, rename

from pathlib import Path

if __name__ == '__main__':
    ignored = []
    with open('polytest', 'r') as f:
        for line in f:
            ignored.append(line.strip())

    for arg in sys.argv[1:]:
        head, tail = path.split(arg)
        if tail in ignored:
            ignored.remove(tail)

    with open('polytest', 'w') as f:
        for file in sorted(ignored):
            print(file, file=f)
