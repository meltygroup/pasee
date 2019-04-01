import pytest

from pasee.storage_backend.demo_backend.sqlite import DemoSqliteStorage


@pytest.fixture
def sqlite_storage():
    return DemoSqliteStorage({"file": ":memory:"})


@pytest.mark.asyncio
async def test_get_authorizations_for_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_authorizations_for_user("")


@pytest.mark.asyncio
async def test_create_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.create_group("")


@pytest.mark.asyncio
async def test_get_groups(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_groups()


@pytest.mark.asyncio
async def test_delete_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.delete_group("")


@pytest.mark.asyncio
async def test_get_users(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_users("")


@pytest.mark.asyncio
async def test_delete_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.delete_user("")


@pytest.mark.asyncio
async def test_get_members_of_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_members_of_group("")


@pytest.mark.asyncio
async def test_group_exists(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.group_exists("")


@pytest.mark.asyncio
async def test_create_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.create_user("")


@pytest.mark.asyncio
async def test_user_exists(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.user_exists("")


@pytest.mark.asyncio
async def test_is_user_in_group(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.is_user_in_group("", "")


@pytest.mark.asyncio
async def test_get_groups_of_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_groups_of_user("")


@pytest.mark.asyncio
async def test_delete_members_in_group(sqlite_storage):
    await sqlite_storage.delete_members_in_group("")


@pytest.mark.asyncio
async def test_get_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.get_user("")


@pytest.mark.asyncio
async def test_ban_user(sqlite_storage):
    with pytest.raises(RuntimeError):
        await sqlite_storage.ban_user("")
