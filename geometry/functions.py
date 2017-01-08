"""Contains helper functions that might be needed by different modules."""


def sign(a: int) -> int:
    """Return the sign of the given number. -1 for negative numbers, 1 for positive numbers and 0 for 0."""
    if a > 0:
        return 1
    if a < 0:
        return -1
    return 0
