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


Users
-----

A user, from a ``Pasee`` point of view can be seen as a tuple of
``(identity_provider, name)``.

Obviously two distinct users can share the same name on two distinct
identity providers, they still are two distinct identities, whence the
"tuple".

So, if a user "John" identifies against ``Pasee``, and ``Pasee`` uses the
``twitter`` backend to proove who he is, he'll be identified as
``"twitter-John"``, so there's no name clash between ``"kisee-John"``, and
``"twitter-John"``.

In a convoluted setup where ``Pasee`` delegates to a ``Kisee`` named
"externals", which delegates to another ``Pasee``, which delegates to
another ``Kisee`` named "internals", you'll receive users identified as
"externals-internals-ada". As you see ``Pasee`` is adding the prefixes,
``Kisee`` does not.

This way you can use a deep and wide setup of ``Kisee``\ s and
``Pasee``\ s, you'll never hit a name-clash, and you'll always be able
to visually spot where a user come from.


Groups
------

Groups naming is hierarchical, separated by dots, like "foo.bar.baz".

Staff members can create any group. One creating a group becomes
staff of its own group, (member of ``my_very_personal_group.staff``).

Staff of a group can:

- Create subgroups, like ``my_very_personal_group.friends``.
- Manage staff of the group.


This applies recursively, let's play it from scratch:

A ``staff`` member (you) creates an ``admin`` group, you become
automatically member of ``admin.staff``.

As a staff member of admin, you create ``admin.developers``, you become
automatically member of ``admin.developers.staff``.

You add a coworker John to ``admin.developers.staff``.

John add three coworkers, Alan, Ada, and Donald to ``admin.developers``.

At this point, only you can create subgroups or manage users / staff
of ``admin``, and only John can create subgroups of ``admin.developers``,
add members to it, or add staff to it.

Hint: You should create a root group per service using ``Pasee``, and
use subgroups to handle authorizations, and root groups for global
authorizations, like:

- articles
  - writers
  - reviewers
- comments
  - moderators
  - ...
- superusers
- ...
