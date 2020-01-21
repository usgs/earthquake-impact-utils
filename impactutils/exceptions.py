class ImpactUtilsError(Exception):
    """Base class for all ImpactUtils exceptions/errors.
    """
    pass


class ConsistentLengthError(ImpactUtilsError):
    """Handles errors when lengths input arrays are not equal."""
    pass


class PDLError(ImpactUtilsError):
    """Handles errors related to pdl."""
    pass


class RequiredArgumentError(ImpactUtilsError):
    """Handles errors for missing arguments."""
    pass


class UnsupportedArgumentError(ImpactUtilsError):
    """Handles errors for unsupported arguments."""
    pass
