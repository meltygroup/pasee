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
            CREATE TABLE IF NOT EXISTS identity(
                name TEXT PRIMARY KEY,
                staff BOOLEAN DEFAULT false
            );
            """
        )
        cursor.execute("CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS identity_in_group(
                id INTEGER PRIMARY KEY,
                identity TEXT,
                groups TEXT
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO identity(
                name, staff
            ) VALUES (
                "kisee-toto", 1
            )
        """
        )
        cursor.execute("INSERT INTO groups(name) VALUES ('superusers')")
        cursor.execute(
            """
            INSERT INTO identity_in_group(
                identity, groups
            ) VALUES (
                "kisee-toto", "superusers"
            )"""
        )

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    async def get_authorizations_for_user(self, identity: str) -> List[str]:
        """Claim list of groups an user belongs to

        We suppose db schema to be created like this:
        $>CREATE TABLE identity(name TEXT PRIMARY KEY);
        $>CREATE TABLE groups(name TEXT PRIMARY KEY);
        $>CREATE TABLE identity_in_group (
            id INTEGER PRIMARY KEY,
            identity TEXT,
            groups TEXT
        );"
        """
        cursor = self.connection.cursor()  # type: ignore
        results = cursor.execute(
            "SELECT groups FROM identity_in_group WHERE identity = :identity",
            {"identity": identity},
        )
        return [elem[0] for elem in results]

    async def staff_creates_group(self, staff, group_name) -> bool:
        """Staff member adds group method
        """
        cursor = self.connection.cursor()  # type: ignore
        # verify user is staff
        result = cursor.execute(
            "SELECT * FROM identity WHERE name = :staff AND staff = 1", {"staff": staff}
        )
        if not result.fetchone():
            return False

        cursor.execute(
            "INSERT INTO groups (name) VALUES (:group_name)", {"group_name": group_name}
        )
        cursor.execute(
            """INSERT INTO identity_in_group(
                identity, groups
            ) VALUES (
                :user, :group_name
            )
            """,
            {"user": staff, "group_name": group_name},
        )

        # add staff to group with user inside
        group_name_staff = group_name + ".staff"
        cursor.execute(
            "INSERT INTO groups (name) VALUES (:group_name)",
            {"group_name": group_name_staff},
        )
        cursor.execute(
            "INSERT INTO identity_in_group(identity, groups) VALUES (:user, :group_name)",
            {"user": staff, "group_name": group_name_staff},
        )
        # returns status
        return True

    async def get_groups(self):
        cursor = self.connection.cursor()
        results = cursor.execute("SELECT * FROM groups")
        groups = results.fetchall()
        cursor.close()
        return groups
