"""HTTP server managing users.
"""


# Version format is: YY.MM[.PATCH] (no leading 0s).
__version__ = "21.4"


class PaseeException(Exception):
    """An exception parent of all Pasee exceptions."""


class MissingSettings(ValueError, PaseeException):
    """A mandatory setting is missing from the configuration file."""


class Unauthorized(PaseeException):
    """An exception raised when someone is *not* authorized to do an action."""

    def __init__(self, reason, **kwargs):
        self.reason = reason
        super().__init__(**kwargs)


class Unauthenticated(PaseeException):
    """An exception used to distinguish incoming requests showing authentication
    and requests without authentication
    """

    def __init__(self, reason, **kwargs):
        self.reason = reason
        super().__init__(**kwargs)
