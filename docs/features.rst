Features
========

Groups
------

Pasee could just gather multiple identity providers, but it add one
optional feature: handling groups.

Groups are typically not given by identity providers: from your point
of view, twitter says "It's this person" not "He's root".


Self-service registration and password reset
--------------------------------------------

``Pasee`` exposes an API for users to register, but it's not its role to
handle identities, so it only forwards blindly those requests to the
*main configured identity provider*, typically a ``Kisee`` instance.


Tokens with authorization scope
-------------------------------

``Pasee`` delivers JWT to your users, a pair of JWT:

- An access token: prooving the identity (and groups) of the user.
- A refresh token: a special token meant only to be used for requesting a new
  access token.

The access token has short TTL while the refresh token has a longer
one, so your clients can use the refresh token to get new access tokens as needed.
The users should never use the refresh token for something else than asking for
a new access token, that's why we're not giving groups in the refresh token.
