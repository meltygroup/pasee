"""Simple dictionary backend
"""
from typing import List

from pasee.groups.backend import AuthorizationBackend


class TestDictionaryStorage(AuthorizationBackend):
    """Exposing a simple backend that fetch authorizations from a dictionary.
    """

    def __init__(self, options: dict, **kwargs) -> None:
        super().__init__(options, **kwargs)  # type: ignore
        self.storage = {
            "kisee-toto": [
                "articles.writers",
                "articles.reviewers",
                "comments.moderators",
            ]
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def get_authorizations_for_user(self, identity: str) -> List[str]:
        """Claim list of groups an user belongs to
        """
        return self.storage.get(identity, [])
