"""Abstract class representing an Identity provider
"""


from abc import ABC, abstractmethod


BACKENDS = {"kisee": "identity_providers.kisee.KiseeIdentityProvider"}


class IdentityProviderBackend(ABC):
    """Abstract class for representing an Identity provider backend
    """

    def __init__(self, settings, **kwargs) -> None:
        self.settings = settings
        super().__init__(**kwargs)  # type: ignore # mypy issue 4335

    @abstractmethod
    async def authenticate_user(self, data) -> dict:
        """Authenticate user
        """
