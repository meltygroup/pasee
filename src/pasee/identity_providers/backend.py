"""Abstract class representing an Identity provider
"""
from abc import ABC, abstractmethod
from typing import Optional


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

    @abstractmethod
    async def get_endpoint(self, action: Optional[str] = None):
        """Get identity backend endpoint for specific action
        Returns root endpoint if action is None
        """

    @abstractmethod
    def get_name(self):
        """Get identity backend name
        """
