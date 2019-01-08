"""sqlite
"""
from typing import List

import asyncpg

from pasee.storage_interface import StorageBackend


class PostgresStorage(StorageBackend):
    """Exposing a simple backend that fetch authorizations from a dictionary.
    """

    def __init__(self, options: dict, **kwargs) -> None:
        super().__init__(options, **kwargs)  # type: ignore
        self.user = options["user"]
        self.password = options["password"]
        self.database = options["database"]
        self.host = options["host"]
        self.port = options["port"]

    async def __aenter__(self):
        self.pool = await asyncpg.create_pool(  # pylint: disable=W0201
            database=self.database,  # W0201 is attribute-defined-outside-init
            user=self.user,  # we define it outside of init on purpose
            password=self.password,
            host=self.host,
            port=self.port,
        )

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            self.pool.terminate()
        except AttributeError:
            pass

    async def get_authorizations_for_user(self, user: str) -> List[str]:
        """Claim list of groups an user belongs to
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                "SELECT group_name FROM user_in_group WHERE username = $1", user
            )
            return [elem[0] for elem in results]

    async def create_group(self, group_name):
        """Staff member adds group method
        """
        async with self.pool.acquire() as connection:
            await connection.execute("INSERT INTO groups(name) VALUES($1)", group_name)

    async def get_groups(self, last_element: str = "") -> List[str]:
        """Get groups paginated by group name in alphabetical order
        List of groups is returned by page of 20
        last_element is the last know element returned in previous page
        So passing the last element to this function will retrieve the next page
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT name
                FROM groups
                WHERE name > $1
                ORDER BY name
                LIMIT 20
                """,
                last_element,
            )
            return [group[0] for group in results]

    async def delete_group(self, group: str):
        """Delete group
        """
        async with self.pool.acquire() as connection:
            connection.execute("DELETE FROM groups WHERE name = $1", group)

    async def get_members_of_group(self, group: str) -> List[str]:
        """Get members of group
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT username
                FROM user_in_group
                WHERE group_name = $1
            """,
                group,
            )
        return [member[0] for member in results]

    async def create_user(self, username):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO users(username) VALUES ($1)
            """,
                username,
            )

    async def group_exists(self, group: str) -> bool:
        async with self.pool.acquire() as connection:
            result = await connection.fetch(
                "SELECT 1 FROM groups WHERE name = $1", group
            )
            return bool(result)

    async def user_exists(self, user: str) -> bool:
        async with self.pool.acquire() as connection:
            result = await connection.fetch(
                "SELECT 1 FROM users WHERE username = $1", user
            )
        return bool(result)

    async def add_member_to_group(self, member, group):
        """Staff adds member to group
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO user_in_group(
                    username, group_name
                ) VALUES (
                    $1, $2
                )
            """,
                member,
                group,
            )

    async def is_user_in_group(self, user: str, group: str) -> bool:
        """Verify that user is in group
        """
        async with self.pool.acquire() as connection:
            result = await connection.execute(
                """
                SELECT 1
                FROM user_in_group
                WHERE
                    group_name = $1
                AND
                    username = $2
            """,
                group,
                user,
            )
            return bool(result)

    async def delete_member_in_group(self, member, group):
        """Delete member in group
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM user_in_group
                WHERE
                    username = $1
                AND
                    group_name = $2
            """,
                member,
                group,
            )
