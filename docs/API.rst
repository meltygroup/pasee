API
===

The API is limited to a few endpoints that tends to self-describe
themselves.

You can get a JSON-Home on ``/`` describing the following resources:

- ``users`` used to manage users
- ``groups`` used to manage groups
- ``tokens`` used by users to create tokens

To test the API you can first create a ``staff`` account:

    python -m pasee --append --groups staff your_username
