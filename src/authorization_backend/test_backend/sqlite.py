"""sqlite
"""
from typing import List

import sqlite3

from pasee.groups.backend import AuthorizationBackend


class TestSqliteStorage(AuthorizationBackend):
    """Exposing a simple backend that fetch authorizations from a dictionary.
    """

    def __init__(self, options: dict, **kwargs) -> None:
        super().__init__(options, **kwargs)
        self.file = options["file"]

    async def __aenter__(self):
        self.connection = sqlite3.connect(self.file)
        cursor = self.connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS identity(name TEXT PRIMARY KEY);")
        cursor.execute("CREATE TABLE IF NOT EXISTS groups(name TEXT PRIMARY KEY);")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS identity_in_group(id INTEGER PRIMARY KEY, identity TEXT, groups TEXT);"
        )

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    async def get_authorizations_for_user(self, identity: str) -> List[str]:
        """Claim list of groups an user belongs to

        We suppose db schema to be created like this:
        $>CREATE TABLE identity(name TEXT PRIMARY KEY);
        $>CREATE TABLE groups(name TEXT PRIMARY KEY);
        $>CREATE TABLE identity_in_group (id INTEGER PRIMARY KEY, identity TEXT, groups TEXT);"
        """
        cursor = self.connection.cursor()
        results = cursor.execute(
            "SELECT groups FROM identity_in_group WHERE identity = :identity",
            {"identity": identity},
        )
        return [elem[0] for elem in results]
