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
            min_size=1,
            max_size=5,
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
                """
                SELECT groups.name
                FROM groups
                JOIN user_in_group
                    ON groups.id = user_in_group.group_id
                JOIN users
                    ON user_in_group.user_id = users.id
                WHERE
                    users.username = $1
                ORDER BY groups.name ASC
                """,
                user,
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

    async def get_groups_of_user(self, user: str, last_element: str = "") -> List[str]:
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT groups.name
                FROM groups
                JOIN user_in_group
                    ON groups.id = user_in_group.group_id
                JOIN users
                    ON user_in_group.user_id = users.id
                WHERE
                    users.username = $1
                    AND groups.name > $2
                ORDER BY groups.name ASC
                LIMIT 20
                """,
                user,
                last_element,
            )
        return [group[0] for group in results]

    async def get_users(self, last_element: str = ""):
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT username
                FROM users
                WHERE username > $1
                ORDER BY username ASC
                LIMIT 50
                """,
                last_element,
            )
            return [group[0] for group in results]

    async def get_user(self, username: str = ""):
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(
                """
                SELECT
                    username,
                    is_banned
                FROM users
                WHERE username = $1
                LIMIT 1
                """,
                username,
            )

            if not result:
                return None

            return {"username": result["username"], "is_banned": result["is_banned"]}

    async def delete_group(self, group: str):
        """Delete group
        """
        await self.delete_members_in_group(group)
        async with self.pool.acquire() as connection:
            await connection.execute("DELETE FROM groups WHERE name = $1", group)

    async def get_members_of_group(self, group: str) -> List[str]:
        """Get members of group
        """
        async with self.pool.acquire() as connection:
            results = await connection.fetch(
                """
                SELECT users.username
                FROM user_in_group
                JOIN users ON users.id = user_in_group.user_id
                JOIN groups ON groups.id = user_in_group.group_id
                WHERE groups.name = $1
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

    async def delete_user(self, username):
        async with self.pool.acquire() as connection:

            await connection.execute(
                """
                DELETE FROM user_in_group
                USING users
                WHERE user_in_group.user_id = users.id
                AND users.username = $1
                """,
                username,
            )
            await connection.execute("DELETE FROM users WHERE username = $1", username)

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
                INSERT INTO user_in_group (user_id, group_id)
                SELECT users.id, groups.id
                FROM users, groups
                WHERE users.username = $1
                AND groups.name = $2
                """,
                member,
                group,
            )

    async def is_user_in_group(self, user: str, group: str) -> bool:
        """Verify that user is in group
        """
        async with self.pool.acquire() as connection:
            result = await connection.fetch(
                """
                SELECT 1
                FROM user_in_group
                JOIN users ON users.id = user_in_group.user_id
                JOIN groups ON groups.id = user_in_group.group_id
                WHERE groups.name = $1
                AND users.username = $2
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
                DELETE FROM user_in_group USING users, groups
                WHERE user_in_group.user_id = users.id
                  AND user_in_group.group_id = groups.id
                  AND users.username = $1
                  AND groups.name = $2
            """,
                member,
                group,
            )

    async def delete_members_in_group(self, group):
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                DELETE FROM user_in_group USING groups
                WHERE user_in_group.group_id = groups.id
                  AND groups.name = $1
                """,
                group,
            )

    async def ban_user(self, username: str, ban: bool = True):
        """Ban user
        """
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                UPDATE users
                SET is_banned = $1
                WHERE username = $2
                """,
                ban,
                username,
            )
