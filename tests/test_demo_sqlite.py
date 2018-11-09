from asyncio import run

import pytest

from pasee.storage_backend.test_backend.sqlite import TestSqliteStorage


@pytest.fixture
def sqlite_storage():
    return TestSqliteStorage({"file": ":memory:"})


def test_get_authorizations_for_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.get_authorizations_for_user(""))


def test_create_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.create_group(""))


def test_get_groups(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.get_groups())


def test_delete_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.delete_group(""))


def test_get_members_of_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.get_members_of_group(""))


def test_group_exists(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.group_exists(""))


def test_create_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.create_user(""))


def test_user_exists(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.user_exists(""))


def test_is_user_in_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        run(sqlite_storage.is_user_in_group("", ""))
