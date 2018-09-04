"""Abstract class representing an Identity provider
"""


from abc import ABC, abstractmethod
from importlib import import_module
from typing import Type


BACKENDS = {"kisee": "identity_providers.kisee.KiseeIdentityProvider"}


class IdentityProviderBackend(ABC):
    """Abstract class for representing an Identity provider backend
    """

    def __init__(self, settings) -> None:
        self.settings = settings
        super().__init__()

    @abstractmethod
    async def authenticate_user(self, data) -> dict:
        """Authenticate user
        """


def import_identity_provider_backend(dotted_path: str) -> Type[IdentityProviderBackend]:
    """Import a dotted module path and return the attribute/class
    designated by the last name in the path. Raise ImportError if the
    import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err
