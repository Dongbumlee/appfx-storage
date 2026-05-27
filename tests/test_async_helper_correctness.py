from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

import pytest

from appfx.storage.blob import AsyncStorageBlobHelper
from appfx.storage.queue import AsyncStorageQueueHelper


class AsyncIterableStub:
    def __init__(self, items: Iterable[Any]) -> None:
        self._items = iter(items)

    def __aiter__(self) -> "AsyncIterableStub":
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._items)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class RecordingBlobService:
    def __init__(self, containers: list[Any]) -> None:
        self.containers = containers
        self.list_kwargs: dict[str, Any] | None = None

    def list_containers(self, **kwargs: Any) -> AsyncIterableStub:
        self.list_kwargs = kwargs
        return AsyncIterableStub(self.containers)


class RecordingQueueService:
    def __init__(self, queues: list[Any]) -> None:
        self.queues = queues
        self.list_kwargs: dict[str, Any] | None = None

    def list_queues(self, **kwargs: Any) -> AsyncIterableStub:
        self.list_kwargs = kwargs
        return AsyncIterableStub(self.queues)


class UploadRecordingBlobHelper(AsyncStorageBlobHelper):
    def __init__(self) -> None:
        super().__init__(account_name="example", credential=object())
        self.upload_calls: list[dict[str, Any]] = []

    async def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: bytes | str,
        overwrite: bool = False,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        max_concurrency: int = 4,
    ) -> dict[str, Any]:
        self.upload_calls.append(
            {
                "container_name": container_name,
                "blob_name": blob_name,
                "data": data,
                "overwrite": overwrite,
                "content_type": content_type,
                "metadata": metadata,
                "max_concurrency": max_concurrency,
            }
        )
        return {"etag": "abc"}


@pytest.mark.asyncio
async def test_async_list_containers_forwards_filters_and_metadata_flag() -> None:
    service = RecordingBlobService(
        [
            SimpleNamespace(
                name="data-raw",
                last_modified="2025-01-01",
                metadata={"owner": "analytics"},
                lease=None,
                public_access=None,
            )
        ]
    )
    helper = AsyncStorageBlobHelper(account_name="example", credential=object())
    helper._blob_service_client = service

    containers = await helper.list_containers(
        name_starts_with="data-", include_metadata=True
    )

    assert service.list_kwargs == {
        "name_starts_with": "data-",
        "include_metadata": True,
    }
    assert containers == [
        {
            "name": "data-raw",
            "last_modified": "2025-01-01",
            "lease": None,
            "public_access": None,
            "metadata": {"owner": "analytics"},
        }
    ]


@pytest.mark.asyncio
async def test_async_list_containers_omits_metadata_by_default() -> None:
    service = RecordingBlobService(
        [
            SimpleNamespace(
                name="logs",
                last_modified="2025-01-01",
                metadata={"owner": "ops"},
                lease=None,
                public_access=None,
            )
        ]
    )
    helper = AsyncStorageBlobHelper(account_name="example", credential=object())
    helper._blob_service_client = service

    containers = await helper.list_containers()

    assert service.list_kwargs == {
        "name_starts_with": None,
        "include_metadata": False,
    }
    assert "metadata" not in containers[0]


@pytest.mark.asyncio
async def test_async_list_queues_forwards_filters_and_metadata_flag() -> None:
    service = RecordingQueueService(
        [SimpleNamespace(name="task-high", metadata={"priority": "high"})]
    )
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = service

    queues = await helper.list_queues(name_starts_with="task-", include_metadata=True)

    assert service.list_kwargs == {
        "name_starts_with": "task-",
        "include_metadata": True,
    }
    assert queues == [{"name": "task-high", "metadata": {"priority": "high"}}]


@pytest.mark.asyncio
async def test_async_list_queues_omits_metadata_by_default() -> None:
    service = RecordingQueueService(
        [SimpleNamespace(name="task-low", metadata={"priority": "low"})]
    )
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = service

    queues = await helper.list_queues()

    assert service.list_kwargs == {
        "name_starts_with": None,
        "include_metadata": False,
    }
    assert queues == [{"name": "task-low"}]


@pytest.mark.asyncio
async def test_upload_blob_from_text_returns_bool_and_forwards_encoded_content() -> (
    None
):
    helper = UploadRecordingBlobHelper()

    result = await helper.upload_blob_from_text(
        "documents",
        "readme.txt",
        "hello",
        encoding="utf-16",
        content_type="text/markdown",
        overwrite=False,
    )

    assert result is True
    assert helper.upload_calls == [
        {
            "container_name": "documents",
            "blob_name": "readme.txt",
            "data": "hello".encode("utf-16"),
            "overwrite": False,
            "content_type": "text/markdown",
            "metadata": None,
            "max_concurrency": 4,
        }
    ]
