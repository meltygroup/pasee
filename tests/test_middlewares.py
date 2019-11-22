import json

import pytest
from aioresponses import aioresponses

from pasee.pasee import identification_app
from pasee.__main__ import load_conf
import mocks


@pytest.fixture
def client(loop, aiohttp_client):
    app = identification_app(settings=load_conf("tests/test-settings.toml"))
    return loop.run_until_complete(aiohttp_client(app))


async def test_bad_json(client):
    response = await client.request(
        "POST",
        "/groups/",
        data=b'{"group" "my_group"}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status == 400
