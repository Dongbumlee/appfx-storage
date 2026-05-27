# appfx-storage

[![CI](https://img.shields.io/github/actions/workflow/status/Dongbumlee/appfx-storage/ci.yml?branch=main&label=CI)](https://github.com/Dongbumlee/appfx-storage/actions/workflows/ci.yml) [![PyPI version](https://img.shields.io/pypi/v/appfx-storage.svg)](https://pypi.org/project/appfx-storage/)

Python helpers for Azure Storage Blob and Queue operations.

The `appfx-storage` package exposes the `appfx.storage` import namespace. It
wraps common Azure Blob Storage and Azure Queue Storage tasks with sync and
async helper classes, typed package metadata, and release-ready packaging.

## Features

- Blob container and blob upload, download, listing, delete, metadata, and SAS
  URL helpers.
- Queue create, send, receive, peek, update, delete, clear, and worker-pattern
  helpers.
- Sync and async clients for both blob and queue operations.
- Azure credential support through connection strings, account names, managed
  identity, and `DefaultAzureCredential`.
- Python 3.12 and 3.13 support.

## Installation

```bash
python -m pip install appfx-storage
```

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Quickstart

Set the storage account name before running examples. When `account_name`
is provided, the helpers use Azure Identity `DefaultAzureCredential`, so local
development can authenticate with Azure CLI and Azure-hosted apps can use
managed identity. Connection strings are supported, but examples intentionally
prefer Entra ID authentication.

```bash
export AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
az login
```

Do not commit `.env` files, connection strings, account keys, or generated SAS
URLs.

## Async blob usage

```python
import asyncio
import os

from appfx.storage import AsyncStorageBlobHelper


async def main() -> None:
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    async with AsyncStorageBlobHelper(account_name=account_name) as helper:
        await helper.create_container("documents")
        await helper.upload_blob("documents", "hello.txt", "Hello from appfx-storage")
        blobs = await helper.list_blobs("documents")
        print([blob["name"] for blob in blobs])


asyncio.run(main())
```

## Sync blob usage

```python
import os

from appfx.storage import StorageBlobHelper


helper = StorageBlobHelper(account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"])
helper.create_container("documents")
helper.upload_blob("documents", "hello.txt", "Hello from appfx-storage")
print(helper.list_blobs("documents"))
```

## Async queue usage

```python
import asyncio
import os

from appfx.storage import AsyncStorageQueueHelper


async def main() -> None:
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    async with AsyncStorageQueueHelper(account_name=account_name) as helper:
        await helper.create_queue("jobs")
        result = await helper.send_message("jobs", {"task": "process-file"})
        print(f"Sent message: {result['message_id']}")
        messages = await helper.receive_messages("jobs")
        print([message["message_id"] for message in messages])


asyncio.run(main())
```

## Sync queue usage

```python
import os

from appfx.storage import StorageQueueHelper


helper = StorageQueueHelper(account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"])
helper.create_queue("jobs")
result = helper.send_message("jobs", {"task": "process-file"})
print(f"Next visible at: {result['next_visible_on']}")
print([message["message_id"] for message in helper.peek_messages("jobs")])
```

## Tests and quality checks

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov
python -m build
python -m twine check dist/*
```

Live Azure tests and examples require your own Azure Storage account and
credentials. Keep live credentials out of source control and CI logs.

## Release notes

- Package name: `appfx-storage`
- Import namespace: `appfx.storage`
- Repository: <https://github.com/Dongbumlee/appfx-storage>
- PyPI publishing is configured for trusted publishing from GitHub Actions on
  published releases and manual workflow dispatch.

## License

MIT License - see [LICENSE](LICENSE) for details.
