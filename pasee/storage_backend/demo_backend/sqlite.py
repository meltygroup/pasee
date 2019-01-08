"""sqlite
"""
from typing import List
import logging
import sqlite3

from pasee.storage_interface import StorageBackend

logger = logging.getLogger(__name__)


class DemoSqliteStorage(StorageBackend):
    """Exposing a simple backend that fetch authorizations from a dictionary.
    """

    def __init__(self, options: dict, **kwargs) -> None:
        super().__init__(options, **kwargs)
        self.file = options["file"]
        self.connection = None

    async def __aenter__(self):
        self.connection = sqlite3.connect(self.file)
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                name TEXT PRIMARY KEY
            );
            """
        )
        cursor.execute("CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_in_group(
                id INTEGER PRIMARY KEY,
                user TEXT,
                group_name TEXT
            );
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX group_name_index
            on groups (name);
            """
        )

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    async def get_authorizations_for_user(self, user: str) -> List[str]:
        """Claim list of groups an user belongs to

        We suppose db schema to be created like this:
        $>CREATE TABLE users(name TEXT PRIMARY KEY);
        $>CREATE TABLE groups(name TEXT PRIMARY KEY);
        $>CREATE TABLE user_in_group (
            id INTEGER PRIMARY KEY,
            user TEXT,
            group_name TEXT
        );"
        """
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        results = cursor.execute(
            "SELECT group_name FROM user_in_group WHERE user = :user", {"user": user}
        )
        return [elem[0] for elem in results]

    async def create_group(self, group_name):
        """Staff member adds group method
        """
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()

        cursor.execute(
            "INSERT INTO groups (name) VALUES (:group_name)", {"group_name": group_name}
        )
        self.connection.commit()

    async def get_groups(self, last_element: str = "") -> List[str]:
        """Get groups paginated by group name in alphabetical order
        List of groups is returned by page of 20
        last_element is the last know element returned in previous page
        So passing the last element to this function will retrieve the next page
        """
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        results = cursor.execute(
            """
            SELECT name
            FROM groups
            WHERE name > :last_element
            ORDER BY name ASC
            LIMIT 20
            """,
            {"last_element": last_element},
        )
        groups = [group[0] for group in results]
        cursor.close()
        return groups

    async def delete_group(self, group: str):
        """Delete group
        """
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM groups WHERE name = :group", {"group": group})
        self.connection.commit()

    async def get_members_of_group(self, group: str) -> List[str]:
        """Get members of group
        """
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()

        query_result = cursor.execute(
            """
            SELECT user
            FROM user_in_group
            WHERE group_name = :group
        """,
            {"group": group},
        )
        members = [member[0] for member in query_result]
        return members

    async def group_exists(self, group: str) -> bool:
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        result = cursor.execute(
            "SELECT 1 FROM groups WHERE name = :group", {"group": group}
        ).fetchone()

        return bool(result)

    async def create_user(self, username):
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO users(name) VALUES(:username)", {"username": username}
        )
        self.connection.commit()

    async def user_exists(self, user: str) -> bool:
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        result = cursor.execute(
            "SELECT 1 FROM users WHERE name = :user", {"user": user}
        ).fetchone()
        return bool(result)

    async def is_user_in_group(self, user: str, group: str) -> bool:
        if self.connection is None:
            raise RuntimeError("This class should be used in a context manager.")
        cursor = self.connection.cursor()
        result = cursor.execute(
            """
                SELECT 1
                FROM user_in_group
                WHERE
                    user = :user
                AND group_name = :group
            """,
            {"user": user, "group": group},
        ).fetchone()
        return bool(result)

    async def add_member_to_group(self, member, group):
        """Staff adds member to group
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_in_group(
                user, group_name
            ) VALUES (
                :user, :group
            )
            """,
            {"user": member, "group": group},
        )
        self.connection.commit()

    async def delete_member_in_group(self, member, group):
        """Delete member in group
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            DELETE FROM user_in_group
            WHERE
                user = :user
            AND group_name = :group
            """,
            {"user": member, "group": group},
        )
        self.connection.commit()
