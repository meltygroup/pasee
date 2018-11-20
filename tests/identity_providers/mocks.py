"""Mocks
"""


async def twitter_get_request_token(self, data, step=1):
    self.oauth_token = "oauth_token_example"
    self.oauth_token_secret = "oauth_token_secret_example"
    return self.oauth_token, self.oauth_token_secret, {}
