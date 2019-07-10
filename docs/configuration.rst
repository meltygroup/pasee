Configuration
=============

``Pasee`` uses a `toml <https://github.com/toml-lang/toml>`__
configuration file like::

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
