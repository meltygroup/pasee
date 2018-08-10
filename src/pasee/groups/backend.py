"""Abstract class representing an Authorization backend
"""


from abc import ABC, abstractmethod
from importlib import import_module
from typing import AsyncContextManager, List, Type


class AuthorizationBackend(ABC, AsyncContextManager):  # pragma: no cover
    """Abstract class for representing an Authorization backend
    """

    def __init__(self, options: dict) -> None:
        self.options = options
        super().__init__()

    @abstractmethod
    async def get_authorizations_for_user(self, identity) -> List[str]:
        """get list the list of group a user identity belongs to
        """


def import_authorization_backend(dotted_path: str) -> Type[AuthorizationBackend]:
    """Import a dotted module path and return the attribute/class
    designated by the last name in the path. Raise ImportError if the
    import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err
