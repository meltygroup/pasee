"""Utils for handling identity providers
"""
from pasee.utils import import_class

BACKENDS = {"kisee": "pasee.identity_providers.kisee.KiseeIdentityProvider"}


def get_identity_provider_with_capability(idps_settings, capability):
    """Returns an identity provider with capability passed in argument
    """
    main_idp = next(
        idp
        for key, idp in idps_settings.items()
        if capability in idp.get("capabilities", set())
    )
    identity_provider_path = BACKENDS.get(main_idp["name"], None)
    identity_provider_settings = idps_settings.get(main_idp["name"], None)
    return import_class(identity_provider_path)(identity_provider_settings)
