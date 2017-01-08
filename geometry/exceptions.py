"""Contains all the exceptions thrown by geometry classes."""


class GeometryException(Exception):
    """The base geometry exception every other exception bases on."""

    pass


class DegeneratedCaseException(GeometryException):
    """An exception thrown for degenerated cases.

    Those cases include trying to construct a line through two points which are
    the same.
    """


class NotInGeneralPositionException(GeometryException):
    """A base exception for general position violations."""

    pass


class ThreePointsAreCollinearException(NotInGeneralPositionException):
    """Exception thrown if three colinear points are encountered."""

    pass


class BoundedFunnelMustNotBeConcaveException(GeometryException):
    """Exception to be thrown if a bounded funnel is concave."""

    pass


class TooFewPointsException(GeometryException):
    """Exception to be thrown if a bounded funnel is concave."""

    pass
