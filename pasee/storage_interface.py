"""Abstract class representing Storage backend
"""


from abc import abstractmethod
from typing import AsyncContextManager, List, Any


class StorageBackend(AsyncContextManager):  # pylint: disable=inherit-non-class
    # (see https://github.com/PyCQA/pylint/issues/2472)
    """Abstract class for representing an Storage backend
    """

    def __init__(self, options: dict, **kwargs: Any) -> None:
        self.options = options
        super().__init__(**kwargs)  # type: ignore # mypy issue 4335

    @abstractmethod
    async def get_authorizations_for_user(self, user) -> List[str]:
        """get list the list of group a user identity belongs to
        """

    @abstractmethod
    async def create_group(self, group_name):
        """Add group
        """

    @abstractmethod
    async def get_groups(self, last_element: str = "") -> List[str]:
        """Get groups paginated by group name in alphabetical order
        List of groups is returned by page of 20
        last_element is the last know element returned in previous page
        So passing the last element to this function will retrieve the next page
        """

    @abstractmethod
    async def get_groups_of_user(self, user: str, last_element: str = "") -> List[str]:
        """Get groups of user
        """

    @abstractmethod
    async def delete_group(self, group: str):
        """Delete group
        """

    @abstractmethod
    async def get_users(self, last_element: str = ""):
        """Get users
        """

    @abstractmethod
    async def get_user(self, username: str = ""):
        """Get user
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
    async def create_user(self, username):
        """Create user
        """

    @abstractmethod
    async def delete_user(self, username):
        """Delete user
        """

    @abstractmethod
    async def is_user_in_group(self, user, group) -> bool:
        """Verify that user is in group
        """

    @abstractmethod
    async def add_member_to_group(self, member, group) -> bool:
        """
        staff adds member to group
        """

    @abstractmethod
    async def delete_member_in_group(self, member, group):
        """Delete member in group
        """

    @abstractmethod
    async def delete_members_in_group(self, group):
        """Delete all members of group
        """

    @abstractmethod
    async def ban_user(self, username: str, ban: bool = True):
        """Ban user
        """
