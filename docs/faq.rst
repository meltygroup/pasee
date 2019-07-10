FAQ
===

How to configure Pasee to use my LDAP server?
---------------------------------------------

Setup an instance of ``Kisee`` to use it (not implemented yet), and add
this ``Kisee`` instance in the ``identity_providers`` of your ``Pasee``
instance.

In your `Kisee` backend you could even expose groups or any
meta-informations stored in your LDAP server as JWT claims. Those
claims have to be whitelisted in ``Pasee`` configuration to be kept in
``Pasee``-signed tokens (By default, we only trust identities, from
identities backends).


Why a ``Kisee`` identity backend settings uses an array of public keys?
-----------------------------------------------------------------------

To help you rotate a ``Kisee`` private key by allowing both during the
transition.


Can Pasee expose an OAuth2 or OpenID endpoint?
----------------------------------------------

Yes, feel free to implement it, see current ``Twitter`` and
``Facebook`` implementations.


Can Pasee use multiple instances of ``Kisee`` to hit different identity sources?
--------------------------------------------------------------------------------

Yes, but a single one can handle registrations from Pasee. If you want
to let your user choose on which ``Kisee`` instance they're
registering, use the ``Kisee`` API directly for registration instead
of passing registrations thrue ``Pasee``.


I don't get it, why do I need a private key on ``Kisee`` and another on ``Pasee``?
----------------------------------------------------------------------------------

``Pasee`` can use multiple identity providers (OAuth2, OpenID connect,
``Pasee`` instances), and will even work without a ``Kisee``
backend. As a ``Kisee`` have to sign tokens, and a ``Pasee`` have to
sign tokens too, they both need a private key. You could use the same
private key on every ``Kisee`` and ``Pasee`` instances, it won't break
the implementation. You can obviously use different ones too.
