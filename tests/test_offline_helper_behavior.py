import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import ContentSettings

from appfx.storage.blob import AsyncStorageBlobHelper, StorageBlobHelper
from appfx.storage.blob.config import get_config as get_blob_config
from appfx.storage.queue import AsyncStorageQueueHelper, StorageQueueHelper


def create_sync_queue_helper(queue_service_client: Any) -> StorageQueueHelper:
    helper = object.__new__(StorageQueueHelper)
    helper.queue_service_client = queue_service_client
    helper.logger = logging.getLogger(__name__)
    return helper


def create_sync_blob_helper(blob_service_client: Any) -> StorageBlobHelper:
    helper = object.__new__(StorageBlobHelper)
    helper.blob_service_client = blob_service_client
    helper.config = get_blob_config()
    helper.logger = logging.getLogger(__name__)
    return helper


class RecordingSyncQueueClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []
        self.updated_messages: list[dict[str, Any]] = []
        self.messages = [
            SimpleNamespace(
                id="message-1",
                pop_receipt="receipt-1",
                content='{"kind": "build"}',
                inserted_on="inserted",
                expires_on="expires",
                next_visible_on="visible",
                dequeue_count=1,
            )
        ]

    def send_message(self, content: str, **kwargs: Any) -> SimpleNamespace:
        self.sent_messages.append({"content": content, "kwargs": kwargs})
        return SimpleNamespace(
            id="message-1",
            pop_receipt="receipt-1",
            inserted_on="inserted",
            expires_on="expires",
            next_visible_on="visible",
        )

    def update_message(
        self,
        message_id: str,
        pop_receipt: str,
        **kwargs: Any,
    ) -> SimpleNamespace:
        self.updated_messages.append(
            {"message_id": message_id, "pop_receipt": pop_receipt, "kwargs": kwargs}
        )
        return SimpleNamespace(pop_receipt="receipt-2", next_visible_on="visible-2")

    def receive_messages(self, **_kwargs: Any) -> list[SimpleNamespace]:
        return self.messages

    def peek_messages(self, **_kwargs: Any) -> list[SimpleNamespace]:
        return self.messages


class RecordingSyncQueueService:
    def __init__(self, queue_client: RecordingSyncQueueClient) -> None:
        self.queue_client = queue_client

    def get_queue_client(self, queue_name: str) -> RecordingSyncQueueClient:
        assert queue_name == "jobs"
        return self.queue_client


class RecordingAsyncQueueClient:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []
        self.updated_messages: list[dict[str, Any]] = []
        self.messages = [
            SimpleNamespace(
                id="message-1",
                pop_receipt="receipt-1",
                content='{"kind": "build"}',
                inserted_on="inserted",
                expires_on="expires",
                next_visible_on="visible",
                dequeue_count=1,
            )
        ]

    async def send_message(self, content: str, **kwargs: Any) -> SimpleNamespace:
        self.sent_messages.append({"content": content, "kwargs": kwargs})
        return SimpleNamespace(
            id="message-1",
            pop_receipt="receipt-1",
            inserted_on="inserted",
            expires_on="expires",
            next_visible_on="visible",
        )

    async def update_message(
        self,
        message_id: str,
        **kwargs: Any,
    ) -> SimpleNamespace:
        self.updated_messages.append({"message_id": message_id, "kwargs": kwargs})
        return SimpleNamespace(pop_receipt="receipt-2", next_visible_on="visible-2")

    async def receive_messages(self, **_kwargs: Any) -> Any:
        for message in self.messages:
            yield message

    async def peek_messages(self, **_kwargs: Any) -> list[SimpleNamespace]:
        return self.messages


class RecordingAsyncQueueService:
    def __init__(self, queue_client: RecordingAsyncQueueClient) -> None:
        self.queue_client = queue_client

    def get_queue_client(self, queue_name: str) -> RecordingAsyncQueueClient:
        assert queue_name == "jobs"
        return self.queue_client


class NotFoundPropertiesClient:
    def get_blob_client(self, _blob_name: str) -> "NotFoundPropertiesClient":
        return self

    def get_queue_properties(self, **_kwargs: Any) -> None:
        raise ResourceNotFoundError("missing")

    def get_container_properties(self) -> None:
        raise ResourceNotFoundError("missing")

    def get_blob_properties(self) -> None:
        raise ResourceNotFoundError("missing")


class AsyncNotFoundPropertiesClient:
    def get_blob_client(self, _blob_name: str) -> "AsyncNotFoundPropertiesClient":
        return self

    async def get_queue_properties(self) -> None:
        raise ResourceNotFoundError("missing")

    async def get_container_properties(self) -> None:
        raise ResourceNotFoundError("missing")

    async def get_blob_properties(self) -> None:
        raise ResourceNotFoundError("missing")


class StaticClientService:
    def __init__(self, client: Any) -> None:
        self.client = client

    def get_queue_client(self, _queue_name: str) -> Any:
        return self.client

    def get_container_client(self, _container_name: str) -> Any:
        return self.client


class RecordingSyncBlobClient:
    def __init__(self, content: bytes = b"downloaded") -> None:
        self.content = content
        self.upload_calls: list[dict[str, Any]] = []

    def upload_blob(self, data: Any, **kwargs: Any) -> None:
        uploaded = data.read() if hasattr(data, "read") else data
        self.upload_calls.append({"data": uploaded, "kwargs": kwargs})

    def download_blob(self) -> SimpleNamespace:
        return SimpleNamespace(readall=lambda: self.content)

    def get_blob_properties(self) -> SimpleNamespace:
        return SimpleNamespace(
            size=12,
            last_modified="last-modified",
            etag="etag-1",
            content_settings=SimpleNamespace(
                content_type="text/plain",
                content_encoding="utf-8",
            ),
            blob_tier="Hot",
            blob_type="BlockBlob",
            metadata={"owner": "tests"},
            creation_time="created",
            lease=SimpleNamespace(status="unlocked", state="available"),
        )


class RecordingSyncContainerClient:
    def __init__(self, blob_client: RecordingSyncBlobClient) -> None:
        self.blob_client = blob_client

    def get_blob_client(self, blob_name: str) -> RecordingSyncBlobClient:
        assert blob_name in {"report.json", "artifact.txt"}
        return self.blob_client


class RecordingBlobService:
    def __init__(self, container_client: Any) -> None:
        self.container_client = container_client

    def get_container_client(self, container_name: str) -> Any:
        assert container_name == "documents"
        return self.container_client


class RecordingAsyncBlobClient:
    def __init__(self, content: bytes = b"downloaded") -> None:
        self.content = content
        self.upload_calls: list[dict[str, Any]] = []

    async def upload_blob(self, data: bytes, **kwargs: Any) -> dict[str, Any]:
        self.upload_calls.append({"data": data, "kwargs": kwargs})
        return {"etag": "etag-async", "last_modified": "last-modified"}

    async def download_blob(self) -> Any:
        content = self.content

        class DownloadStream:
            async def readall(self) -> bytes:
                return content

        return DownloadStream()


class RecordingAsyncContainerClient:
    def __init__(self, blob_client: RecordingAsyncBlobClient) -> None:
        self.blob_client = blob_client

    def get_blob_client(self, blob_name: str) -> RecordingAsyncBlobClient:
        assert blob_name in {"events.json", "artifact.txt"}
        return self.blob_client


@pytest.mark.parametrize(
    ("message", "expected_content"),
    [
        ({"kind": "build", "attempt": 1}, json.dumps({"kind": "build", "attempt": 1})),
        (["build", 1], json.dumps(["build", 1])),
        (42, "42"),
        (b"binary-payload", "binary-payload"),
    ],
)
def test_sync_queue_send_message_serializes_supported_content(
    message: Any,
    expected_content: str,
) -> None:
    queue_client = RecordingSyncQueueClient()
    helper = create_sync_queue_helper(RecordingSyncQueueService(queue_client))

    result = helper.send_message(
        "jobs",
        message,
        visibility_timeout=30,
        time_to_live=600,
        timeout=5,
    )

    assert queue_client.sent_messages == [
        {
            "content": expected_content,
            "kwargs": {
                "visibility_timeout": 30,
                "time_to_live": 600,
                "timeout": 5,
            },
        }
    ]
    assert result == {
        "message_id": "message-1",
        "pop_receipt": "receipt-1",
        "inserted_on": "inserted",
        "expires_on": "expires",
        "next_visible_on": "visible",
    }


@pytest.mark.parametrize(
    ("message", "expected_content"),
    [
        ({"kind": "build", "attempt": 1}, json.dumps({"kind": "build", "attempt": 1})),
        (["build", 1], json.dumps(["build", 1])),
        (42, "42"),
        (b"binary-payload", "binary-payload"),
    ],
)
@pytest.mark.asyncio
async def test_async_queue_send_message_serializes_supported_content(
    message: Any,
    expected_content: str,
) -> None:
    queue_client = RecordingAsyncQueueClient()
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = RecordingAsyncQueueService(queue_client)

    result = await helper.send_message(
        "jobs",
        message,
        visibility_timeout=30,
        time_to_live=600,
    )

    assert queue_client.sent_messages == [
        {
            "content": expected_content,
            "kwargs": {
                "visibility_timeout": 30,
                "time_to_live": 600,
            },
        }
    ]
    assert result == {
        "message_id": "message-1",
        "pop_receipt": "receipt-1",
        "inserted_on": "inserted",
        "expires_on": "expires",
        "next_visible_on": "visible",
    }


@pytest.mark.asyncio
async def test_async_queue_update_message_serializes_bytes_like_send_message() -> None:
    queue_client = RecordingAsyncQueueClient()
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = RecordingAsyncQueueService(queue_client)

    result = await helper.update_message(
        "jobs",
        "message-1",
        "receipt-1",
        b"binary-payload",
        visibility_timeout=45,
    )

    assert queue_client.updated_messages == [
        {
            "message_id": "message-1",
            "kwargs": {
                "pop_receipt": "receipt-1",
                "content": "binary-payload",
                "visibility_timeout": 45,
            },
        }
    ]
    assert result == {
        "pop_receipt": "receipt-2",
        "next_visible_on": "visible-2",
    }


def test_sync_queue_update_message_matches_async_response_shape() -> None:
    queue_client = RecordingSyncQueueClient()
    helper = create_sync_queue_helper(RecordingSyncQueueService(queue_client))

    result = helper.update_message(
        "jobs",
        "message-1",
        "receipt-1",
        content="updated",
        visibility_timeout=45,
    )

    assert queue_client.updated_messages == [
        {
            "message_id": "message-1",
            "pop_receipt": "receipt-1",
            "kwargs": {
                "content": "updated",
                "visibility_timeout": 45,
                "timeout": None,
            },
        }
    ]
    assert result == {
        "pop_receipt": "receipt-2",
        "next_visible_on": "visible-2",
    }


@pytest.mark.asyncio
async def test_async_queue_receive_message_uses_message_id_key() -> None:
    queue_client = RecordingAsyncQueueClient()
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = RecordingAsyncQueueService(queue_client)

    result = await helper.receive_message("jobs")

    assert result is not None
    assert result["message_id"] == "message-1"
    assert "id" not in result


@pytest.mark.asyncio
async def test_async_queue_receive_messages_uses_message_id_key() -> None:
    queue_client = RecordingAsyncQueueClient()
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = RecordingAsyncQueueService(queue_client)

    result = await helper.receive_messages("jobs")

    assert result[0]["message_id"] == "message-1"
    assert "id" not in result[0]


@pytest.mark.asyncio
async def test_async_queue_peek_messages_uses_message_id_key() -> None:
    queue_client = RecordingAsyncQueueClient()
    helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    helper._queue_service_client = RecordingAsyncQueueService(queue_client)

    result = await helper.peek_messages("jobs")

    assert result[0]["message_id"] == "message-1"
    assert "id" not in result[0]


def test_sync_queue_receive_messages_uses_message_id_key() -> None:
    queue_client = RecordingSyncQueueClient()
    helper = create_sync_queue_helper(RecordingSyncQueueService(queue_client))

    result = helper.receive_messages("jobs")

    assert result[0]["message_id"] == "message-1"
    assert "id" not in result[0]


def test_sync_queue_peek_messages_uses_message_id_key() -> None:
    queue_client = RecordingSyncQueueClient()
    helper = create_sync_queue_helper(RecordingSyncQueueService(queue_client))

    result = helper.peek_messages("jobs")

    assert result[0]["message_id"] == "message-1"
    assert "id" not in result[0]


def test_sync_queue_message_processor_accepts_receive_messages_shape() -> None:
    queue_client = RecordingSyncQueueClient()
    helper = create_sync_queue_helper(RecordingSyncQueueService(queue_client))
    callback_messages: list[dict[str, Any]] = []

    processor = helper.create_message_processor(
        lambda message: callback_messages.append(message)
    )
    received_message = helper.receive_messages("jobs")[0]
    result = processor(received_message)

    assert result == {"success": True, "result": None}
    assert callback_messages == [
        {
            "message_id": "message-1",
            "content": {"kind": "build"},
            "inserted_on": "inserted",
            "expires_on": "expires",
            "next_visible_on": "visible",
            "dequeue_count": 1,
            "pop_receipt": "receipt-1",
        }
    ]
    assert "id" not in callback_messages[0]
    assert "insertion_time" not in callback_messages[0]
    assert "expiration_time" not in callback_messages[0]


def test_sync_upload_file_detects_content_type_and_forwards_upload_options(
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "report.json"
    source_file.write_text('{"status": "ok"}', encoding="utf-8")
    blob_client = RecordingSyncBlobClient()
    helper = create_sync_blob_helper(
        RecordingBlobService(RecordingSyncContainerClient(blob_client))
    )

    result = helper.upload_file(
        "documents",
        "report.json",
        str(source_file),
        overwrite=True,
        metadata={"owner": "tests"},
    )

    assert result is True
    assert blob_client.upload_calls == [
        {
            "data": b'{"status": "ok"}',
            "kwargs": {
                "overwrite": True,
                "metadata": {"owner": "tests"},
                "content_settings": ContentSettings(content_type="application/json"),
                "standard_blob_tier": None,
            },
        }
    ]


def test_sync_download_and_properties_return_stable_blob_fields() -> None:
    blob_client = RecordingSyncBlobClient(content=b"artifact")
    helper = create_sync_blob_helper(
        RecordingBlobService(RecordingSyncContainerClient(blob_client))
    )

    content = helper.download_blob("documents", "artifact.txt")
    properties = helper.get_blob_properties("documents", "artifact.txt")

    assert content == b"artifact"
    assert properties == {
        "name": "artifact.txt",
        "size": 12,
        "last_modified": "last-modified",
        "etag": "etag-1",
        "content_type": "text/plain",
        "content_encoding": "utf-8",
        "blob_tier": "Hot",
        "blob_type": "BlockBlob",
        "metadata": {"owner": "tests"},
        "creation_time": "created",
        "lease_status": "unlocked",
        "lease_state": "available",
    }


@pytest.mark.asyncio
async def test_async_upload_blob_auto_detects_content_type_and_returns_sdk_fields() -> (
    None
):
    blob_client = RecordingAsyncBlobClient()
    helper = AsyncStorageBlobHelper(account_name="example", credential=object())
    helper._blob_service_client = RecordingBlobService(
        RecordingAsyncContainerClient(blob_client)
    )

    result = await helper.upload_blob(
        "documents",
        "events.json",
        "payload",
        overwrite=True,
        metadata={"owner": "tests"},
        max_concurrency=2,
    )

    assert result == {"etag": "etag-async", "last_modified": "last-modified"}
    assert blob_client.upload_calls == [
        {
            "data": b"payload",
            "kwargs": {
                "overwrite": True,
                "content_settings": ContentSettings(content_type="application/json"),
                "metadata": {"owner": "tests"},
                "max_concurrency": 2,
            },
        }
    ]


@pytest.mark.asyncio
async def test_async_download_blob_returns_stream_content() -> None:
    blob_client = RecordingAsyncBlobClient(content=b"artifact")
    helper = AsyncStorageBlobHelper(account_name="example", credential=object())
    helper._blob_service_client = RecordingBlobService(
        RecordingAsyncContainerClient(blob_client)
    )

    assert await helper.download_blob("documents", "artifact.txt") == b"artifact"


def test_sync_existence_checks_return_false_on_resource_not_found() -> None:
    not_found_client = NotFoundPropertiesClient()
    queue_helper = create_sync_queue_helper(StaticClientService(not_found_client))
    blob_helper = create_sync_blob_helper(StaticClientService(not_found_client))

    assert queue_helper.queue_exists("missing") is False
    assert blob_helper.container_exists("missing") is False
    assert blob_helper.blob_exists("missing", "artifact.txt") is False


@pytest.mark.asyncio
async def test_async_existence_checks_return_false_on_resource_not_found() -> None:
    not_found_client = AsyncNotFoundPropertiesClient()
    queue_helper = AsyncStorageQueueHelper(account_name="example", credential=object())
    blob_helper = AsyncStorageBlobHelper(account_name="example", credential=object())
    queue_helper._queue_service_client = StaticClientService(not_found_client)
    blob_helper._blob_service_client = StaticClientService(not_found_client)

    assert await queue_helper.queue_exists("missing") is False
    assert await blob_helper.container_exists("missing") is False
    assert await blob_helper.blob_exists("missing", "artifact.txt") is False


def test_sync_queue_list_omits_metadata_by_default() -> None:
    class QueueListService:
        def __init__(self) -> None:
            self.list_kwargs: dict[str, Any] | None = None

        def list_queues(self, **kwargs: Any) -> list[SimpleNamespace]:
            self.list_kwargs = kwargs
            return [SimpleNamespace(name="jobs", metadata={"owner": "tests"})]

    service = QueueListService()
    helper = create_sync_queue_helper(service)

    queues = helper.list_queues()

    assert service.list_kwargs == {
        "name_starts_with": None,
        "include_metadata": False,
        "results_per_page": None,
        "timeout": None,
    }
    assert queues == [{"name": "jobs"}]


def test_sync_queue_list_includes_metadata_when_requested_and_present() -> None:
    class QueueListService:
        def __init__(self) -> None:
            self.list_kwargs: dict[str, Any] | None = None

        def list_queues(self, **kwargs: Any) -> list[SimpleNamespace]:
            self.list_kwargs = kwargs
            return [SimpleNamespace(name="jobs", metadata={"owner": "tests"})]

    service = QueueListService()
    helper = create_sync_queue_helper(service)

    queues = helper.list_queues(include_metadata=True)

    assert service.list_kwargs == {
        "name_starts_with": None,
        "include_metadata": True,
        "results_per_page": None,
        "timeout": None,
    }
    assert queues == [{"name": "jobs", "metadata": {"owner": "tests"}}]


def test_sync_blob_list_omits_metadata_by_default_and_forwards_include() -> None:
    class BlobListContainer:
        def __init__(self) -> None:
            self.list_kwargs: dict[str, Any] | None = None

        def list_blobs(self, **kwargs: Any) -> list[SimpleNamespace]:
            self.list_kwargs = kwargs
            return [
                SimpleNamespace(
                    name="artifact.txt",
                    size=8,
                    last_modified="last-modified",
                    etag="etag-1",
                    content_settings=SimpleNamespace(content_type="text/plain"),
                    blob_tier="Hot",
                    blob_type="BlockBlob",
                    metadata={"owner": "tests"},
                )
            ]

    container = BlobListContainer()
    helper = create_sync_blob_helper(RecordingBlobService(container))

    blobs = helper.list_blobs("documents", prefix="artifacts/")

    assert container.list_kwargs == {
        "name_starts_with": "artifacts/",
        "include": None,
    }
    assert blobs == [
        {
            "name": "artifact.txt",
            "size": 8,
            "last_modified": "last-modified",
            "etag": "etag-1",
            "content_type": "text/plain",
            "blob_tier": "Hot",
            "blob_type": "BlockBlob",
        }
    ]
