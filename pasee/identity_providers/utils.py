"""Utils for handling identity providers
"""
from pasee.utils import import_class


def get_identity_provider_with_capability(settings, capability):
    """Returns an identity provider with capability passed in argument
    """
    for idp in settings["identity_providers"]:
        if capability in idp.get("capabilities", set()):
            return import_class(idp["implementation"])(idp)
    return None
