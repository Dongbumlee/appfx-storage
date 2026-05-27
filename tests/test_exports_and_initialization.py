import pytest

import appfx.storage as storage
from appfx.storage.blob import AsyncStorageBlobHelper, StorageBlobHelper
from appfx.storage.queue import AsyncStorageQueueHelper, StorageQueueHelper


def test_top_level_exports_are_available() -> None:
    assert storage.__version__
    assert storage.StorageBlobHelper is StorageBlobHelper
    assert storage.AsyncStorageBlobHelper is AsyncStorageBlobHelper
    assert storage.StorageQueueHelper is StorageQueueHelper
    assert storage.AsyncStorageQueueHelper is AsyncStorageQueueHelper


@pytest.mark.parametrize("helper_type", [StorageBlobHelper, StorageQueueHelper])
def test_sync_helpers_require_connection_information(helper_type: type[object]) -> None:
    with pytest.raises(ValueError, match="Either connection_string or account_name"):
        helper_type()


@pytest.mark.parametrize(
    "helper_type",
    [AsyncStorageBlobHelper, AsyncStorageQueueHelper],
)
@pytest.mark.asyncio
async def test_async_helpers_require_connection_information(
    helper_type: type[AsyncStorageBlobHelper | AsyncStorageQueueHelper],
) -> None:
    helper = helper_type()

    with pytest.raises(ValueError, match="Either connection_string or account_name"):
        await helper._initialize_client()
