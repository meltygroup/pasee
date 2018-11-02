# Pasee — Identity Managment Server

## Name

The name "Pasee", inspired from "Kisee" (the IdM), spoken as the
french phrase "Passez !", `[ˈpɑːsə(ɹ)]`.


## Overview

This service is a simple layer over multiple IdMs, typically a Kisee
and other identity providers like Twitter, Github, …


## Features

### Groups

Pasee has one more reponsibility: it handles groups.

Groups are typically not given by identity providers (from your point
of view, twitter says "It's this person" not "He's root"). But yes,
you're free to *not* use Pasee groups and handle your own ACLs or
groups or whatever in your application.


### Self-service registration / password reset / and so on

`Pasee` exposes in its API means for users to register and so on, but
it's not its rôle to handle this. Pasee only forwards blindly those
requests to the *main identity provider*, typically a `Kisee`
instance.


## Configuration

Pasee uses a [toml](https://github.com/toml-lang/toml) configuration file like:

      host = "0.0.0.0"
      port = 8150

      # Generated using:
      #
      #    openssl ecparam -name secp256k1 -genkey -noout -out secp256k1.pem
      #
      # Yes we know P-256 is a bad one, but for compatibility with JS
      # clients for the moment we can't really do better.
      private_key = """-----BEGIN EC PRIVATE KEY-----
      ..."""

      # Generated using:
      # openssl ec -in secp256k1.pem -pubout > secp256k1.pub
      public_key = """-----BEGIN PUBLIC KEY-----
      MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEEVgsgM7Aliru0XU+OggGC5jxRoZUI4/C
      fsNJ8ZUlTKxjn8VzO4Db2ITFvUdyRCQjGRuq5QRJt7a46ZyfrDb+6w==
      -----END PUBLIC KEY-----"""

      [jwt]
      iss = "pasee.meltylab.fr"

      [[identity_providers]]
      name = "kisee"
      host = "127.0.0.1"
      port = 8140
      protocol = "kisee"
      [identity_providers.settings]
      public_keys = ["""-----BEGIN PUBLIC KEY-----MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEE/WCqajmhfppNUB2uekSxX976fcWA3bbdew8NkUtCoBigl9lWkqfnkF18H9fgG0gafPhGtub23+8Ldulvmf1lg==-----END PUBLIC KEY-----"""]

      [[identity_providers]]
      name = "twitter"
      host = "twitter.com"
      port = 443
      protocol = "oauth2"
      [identity_providers.settings]
      app_id = "..."
      app_secret = "..."


## FAQ

> How to configure `Pasee` to hit my LDAP server?

Two solutions:

Setup an instance of `Kisee` to use it, and add this `Kisee`
instance in the `identity_providers` of your `Pasee` instance.

In your `Kisee` backend you can even expose groups or any
meta-informations stored in your LDAP server as JWT claims. Those
claims have to be whitelisted in `Pasee` configuration to be kept in
`Pasee`-signed tokens (By default, we only trust identities, from
identities backends).


> Why a `Kisee` identity backend settings uses an array of public keys?

To help you rotate a `Kisee` private key by allowing both during the
transition.


> Can Pasee expose an OAuth2 or OpenID endpoint?

Yes, feel free to implement it.


> Can Pasee use multiple instances of Kisee to hit different identity sources?

Yes, but only the first one with register capability set in its configurations
will be used to forward registrations as the users have no way (for the moment)
to choose on which Kisee instance they will be stored, from their point of view
they're registering to the `Pasee` instance without knowing it's forwarding
blindly to a `Kisee`. You can also hard-code your client to register with
a specific Kisee instance directly as the Kisee/Pasee API are the same.


> I don't get it, why do I need a private key on `Kisee` and another on `Pasee`?

`Pasee` can use multiple identity providers (OAuth2, OpenID connect,
`Pasee` instances), and will even work without a `Kisee` backend. As a
`Kisee` have to sign tokens, and a `Pasee` have to sign tokens, they
both need a private key. You could use the same private key on every
`Kisee` and `Pasee` instances, it won't break the implementation. You
can obviously use different ones too. As you prefer.


## Running

You'll need a `settings.toml` file (see Settings section).

And start the server using:

```
python3 -m pasee
```


## Contributing

To setup a dev environment, create a venv and run:

```
python3 -m pip install -e .[dev]
```

And run it using:

```
python3 -m pasee
```


## API

The admin should be mounted on `/admin/`. Users in the `staff` group
can login to it. You'll have to create the first `staff` user from
command-line using:

    python3 -m pasee --append --groups staff your_username


The API exposes the following resources:

- A home on `/` (GET).
- JSON web tokens on `/tokens/` (GET, POST).
- Groups handling on `/groups/`.


## Users

A user, from a `Pasee` point of view can be seen as a tuple of
`(identity_provider, name)`.

Obviously two distinct users can share the same "name" on two distinct
identity providers, they still are two distinct identities, whence the
"tuple".

So, if a user "John" identifies against `Pasee`, and `Pasee` uses the
`twitter` backend to proove who he is, he'll be identified as
`"twitter-John"`, so there's no name clash between `"kisee-John"`, and
`"twitter-John"`.

In a convoluted setup where `Pasee` delegates to a `Kisee` named
"externals", which delegates to another `Pasee`, which delegates to
another `Kisee` named "internals", you'll receive users identified as
"externals-internals-ada". As you see `Pasee` is adding the prefixes,
`Kisee` does not.

This way you can use a deep and wide setup of `Kisee`s and `Pasee`s,
you'll never hit a name-clash, and you'll always be able to visually
spot where a user come from.


## Groups

Groups naming is hierarchical, separated by dots, like "foo.bar.baz".

Staff members can create any group. One creating a group becomes
staff of its own group, (member of `my_very_personal_group.staff`).

Staff of a group can:
 - Create subgroups, like `my_very_personal_group.friends`.
 - Manage staff of the group.


This applies recursively, let's play it from scratch:

A `staff` member (you) creates an `admin` group, you become
automatically member of `admin.staff`.

As a staff member of admin, you create `admin.developers`, you become
automatically member of `admin.developers.staff`.

You add a coworker John to `admin.developers.staff`.

John add three coworkers, Alan, Ada, and Donald to `admin.developers`.

At this point, only you can create subgroups or manage users / staff
of `admin`, and only John can create subgroups of `admin.developers`,
add members to it, or add staff to it.

Hint: You should create a root group per service using `Pasee`, and
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


# TODO

- Admin interface
- Status page
- Self-service registration.
- Token invalidation (`DELETE /jwt{/jti}`).
- Self-service password reset.
- Rate-limiting?
- Better error messages (Maybe https://github.com/blongden/vnd.error?)
