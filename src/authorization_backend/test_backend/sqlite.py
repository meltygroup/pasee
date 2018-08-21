"""sqlite
"""
from typing import List

import sqlite3

from pasee.groups.backend import AuthorizationBackend


class TestSqliteStorage(AuthorizationBackend):
    """Exposing a simple backend that fetch authorizations from a dictionary.
    """

    def __init__(self, options: dict, **kwargs) -> None:
        super().__init__(options, **kwargs)  # type: ignore
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
            INSERT INTO users(
                name
            ) VALUES (
                "kisee-toto"
            )
        """
        )
        cursor.execute("INSERT INTO groups(name) VALUES ('staff')")
        cursor.execute(
            """
            INSERT INTO user_in_group(
                user, group_name
            ) VALUES (
                "kisee-toto", "staff"
            )"""
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
        cursor = self.connection.cursor()  # type: ignore
        results = cursor.execute(
            "SELECT group_name FROM user_in_group WHERE user = :user", {"user": user}
        )
        return [elem[0] for elem in results]

    async def staff_creates_group(self, staff, group_name) -> bool:
        """Staff member adds group method
        """
        cursor = self.connection.cursor()  # type: ignore

        cursor.execute(
            "INSERT INTO groups (name) VALUES (:group_name)", {"group_name": group_name}
        )
        cursor.execute(
            """INSERT INTO user_in_group(
                user, group_name
            ) VALUES (
                :user, :group_name
            )
            """,
            {"user": staff, "group_name": group_name},
        )

        group_name_staff = group_name + ".staff"
        cursor.execute(
            "INSERT INTO groups (name) VALUES (:group_name)",
            {"group_name": group_name_staff},
        )
        cursor.execute(
            "INSERT INTO user_in_group(user, group_name) VALUES (:user, :group_name)",
            {"user": staff, "group_name": group_name_staff},
        )
        return True

    async def get_groups(self) -> List[str]:
        """Get all groups
        """
        cursor = self.connection.cursor()
        results = cursor.execute("SELECT name FROM groups")
        groups = results.fetchall()
        cursor.close()
        return groups

    async def get_members_of_group(self, group: str) -> List[str]:
        """Get members of group
        """
        cursor = self.connection.cursor()  # type: ignore

        query_result = cursor.execute(
            """
            SELECT user
            FROM user_in_group
            WHERE group_name = :group
        """,
            {"group": group},
        )
        return query_result.fetchall()

    async def group_exists(self, group: str) -> bool:
        cursor = self.connection.cursor()  # type: ignore
        result = cursor.execute(
            "SELECT 1 FROM groups WHERE name = :group", {"group": group}
        ).fetchone()
        print(result)
        return True if result else False
