from asyncio import run

import pytest

from pasee.storage_backend.test_backend.sqlite import TestSqliteStorage


@pytest.fixture
def sqlite_storage():
    return TestSqliteStorage({"file": ":memory:"})


def test_get_authorizations_for_user__not_run_in_context_manager(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.get_authorizations_for_user(""))
