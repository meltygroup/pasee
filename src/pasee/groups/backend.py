"""Abstract class representing an Authorization backend
"""


from abc import abstractmethod
from importlib import import_module
from typing import AsyncContextManager, List, Type


class AuthorizationBackend(
    AsyncContextManager
):  # pragma: no cover pylint: disable=inherit-non-class
    # (see https://github.com/PyCQA/pylint/issues/2472)
    """Abstract class for representing an Authorization backend
    """

    def __init__(self, options: dict) -> None:
        self.options = options
        super().__init__()

    @abstractmethod
    async def get_authorizations_for_user(self, user) -> List[str]:
        """get list the list of group a user identity belongs to
        """

    @abstractmethod
    async def staff_creates_group(self, staff, group_name) -> bool:
        """Add group
        """

    @abstractmethod
    async def get_groups(self) -> List[str]:
        """Get all groups
        """

    @abstractmethod
    async def get_members_of_group(self, group) -> List[str]:
        """Get members of group
        """

    @abstractmethod
    async def group_exists(self, group) -> bool:
        """Assert group exists
        """

    @abstractmethod
    async def user_exists(self, user) -> bool:
        """Assert user exists
        """

    @abstractmethod
    async def add_member_to_group(self, member, group) -> bool:
        """
        staff adds member to group
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
