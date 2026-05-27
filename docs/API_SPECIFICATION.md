# appfx-storage API Reference

This document provides the complete API reference for `appfx-storage`, a Python helper library for Azure Storage Blob and Queue operations.

## Overview

The `appfx.storage` package provides both synchronous and asynchronous clients for Azure Storage operations with enhanced authentication, SAS token generation, and error handling capabilities.

## Table of Contents

- [Blob Storage Client](#blob-storage-client)
  - [AsyncStorageBlobHelper](#asyncstorageblobhelper)
  - [StorageBlobHelper](#storageblobhelper)
- [Queue Storage Client](#queue-storage-client)
  - [AsyncStorageQueueHelper](#asyncstoragequeuehelper)
  - [StorageQueueHelper](#storagequeuehelper)
- [Configuration](#configuration)
- [Exceptions](#exceptions)
- [Data Models](#data-models)
- [Examples](#examples)

## Blob Storage Client

The blob storage client provides operations for managing containers and blobs in Azure Storage. The library offers both asynchronous and synchronous implementations.

### AsyncStorageBlobHelper

Asynchronous client for Azure Blob Storage operations.

#### Constructor

```python
class AsyncStorageBlobHelper:
    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        credential: Optional[Any] = None,
        config: Optional[Union[dict[str, Any], Any]] = None
    ) -> None
```

Creates a new instance of the AsyncStorageBlobHelper.

##### Parameters

| Name                | Type            | Description                                                          | Default  |
| ------------------- | --------------- | -------------------------------------------------------------------- | -------- |
| `connection_string` | `str` \| `None` | Complete Azure Storage connection string.                            | `None`   |
| `account_name`      | `str` \| `None` | Azure Storage account name. Required if not using connection_string. | `None`   |
| `credential`        | `Any` \| `None` | Azure credential object (DefaultAzureCredential, etc.).              | `None`   |
| `config`            | `dict[str, Any]` \| `Any` \| `None` | Configuration object or dictionary for custom settings. | `None` |

##### Exceptions

| Exception             | Description                                                         |
| --------------------- | ------------------------------------------------------------------- |
| `ValueError`          | Raised when neither account_name nor connection_string is provided. |
| `ClientAuthenticationError` | Raised by the Azure SDK when authentication fails.          |

---

### Container Operations

#### create_container

```python
async def create_container(
    self,
    container_name: str,
    public_access: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> bool
```

Creates a new container in the storage account.

##### Parameters

| Name             | Type                       | Description                                                          | Default  |
| ---------------- | -------------------------- | -------------------------------------------------------------------- | -------- |
| `container_name` | `str`                      | Name of the container to create. Must be 3-63 characters, lowercase. | Required |
| `public_access`  | `str` \| `None`            | Public access level: `"blob"`, `"container"`, or `None`.             | `None`   |
| `metadata`       | `Dict[str, str]` \| `None` | User-defined metadata as key-value pairs.                            | `None`   |

##### Returns

| Type   | Description                                       |
| ------ | ------------------------------------------------- |
| `bool` | `True` if the container was created successfully. |

##### Exceptions

| Exception             | Description                           |
| --------------------- | ------------------------------------- |
| `ValueError`          | Invalid container name or parameters. |
| `ResourceExistsError` | Container already exists.             |
| `HttpResponseError`   | Azure service error occurred.         |

##### Example

```python
from appfx.storage import AsyncStorageBlobHelper

async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    # Create a private container
    await client.create_container("documents")
    
    # Create a public container with metadata
    await client.create_container(
        "images",
        public_access="blob",
        metadata={"purpose": "public-images", "owner": "team-a"}
    )
```

---

#### delete_container

```python
async def delete_container(
    self,
    container_name: str,
    force_delete: bool = False
) -> bool
```

Deletes an existing container. By default, deletion fails if the container is
not empty; pass `force_delete=True` to delete blobs first.

##### Parameters

| Name             | Type  | Description                      | Default  |
| ---------------- | ----- | -------------------------------- | -------- |
| `container_name` | `str` | Name of the container to delete. | Required |
| `force_delete`   | `bool` | Delete existing blobs before deleting the container. | `False` |

##### Returns

| Type   | Description                                       |
| ------ | ------------------------------------------------- |
| `bool` | `True` if the container was deleted successfully. |

##### Exceptions

| Exception               | Description                   |
| ----------------------- | ----------------------------- |
| `ResourceNotFoundError` | Container does not exist.     |
| `HttpResponseError`     | Azure service error occurred. |

##### Example

```python
from appfx.storage import AsyncStorageBlobHelper

async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    success = await client.delete_container("old-empty-container")
    print(f"Container deleted: {success}")
```

---

#### list_containers

```python
async def list_containers(
    self,
    name_starts_with: Optional[str] = None,
    include_metadata: bool = False
) -> List[Dict[str, Any]]
```

Lists all containers in the storage account.

##### Parameters

| Name               | Type            | Description                            | Default |
| ------------------ | --------------- | -------------------------------------- | ------- |
| `name_starts_with` | `str` \| `None` | Filter containers by name prefix.      | `None`  |
| `include_metadata` | `bool`          | Include container metadata in results. | `False` |

##### Returns

| Type                  | Description                            |
| --------------------- | -------------------------------------- |
| `List[Dict[str, Any]]` | List of container information dictionaries. |

##### Example

```python
from appfx.storage import AsyncStorageBlobHelper

async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    # List all containers
    containers = await client.list_containers()
    
    # List containers starting with "data" and include metadata
    data_containers = await client.list_containers(
        name_starts_with="data",
        include_metadata=True
    )
    
    for container in containers:
        print(f"Container: {container['name']}")
```

---

#### container_exists

```python
async def container_exists(self, container_name: str) -> bool
```

Checks if a container exists in the storage account.

##### Parameters

| Name             | Type  | Description                     | Default  |
| ---------------- | ----- | ------------------------------- | -------- |
| `container_name` | `str` | Name of the container to check. | Required |

##### Returns

| Type   | Description                                        |
| ------ | -------------------------------------------------- |
| `bool` | `True` if the container exists, `False` otherwise. |

##### Example

```python
from appfx.storage import AsyncStorageBlobHelper

async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    if await client.container_exists("documents"):
        print("Container exists")
    else:
        await client.create_container("documents")
```

---

### Blob Operations

#### upload_blob

```python
async def upload_blob(
    self,
    container_name: str,
    blob_name: str,
    data: bytes | str,
    overwrite: bool = False,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
    max_concurrency: int = 4,
) -> dict[str, Any]
```

Uploads data to a blob in the specified container.

##### Parameters

| Name              | Type                       | Description                                                     | Default  |
| ----------------- | -------------------------- | --------------------------------------------------------------- | -------- |
| `container_name`  | `str`                      | Target container name.                                          | Required |
| `blob_name`       | `str`                      | Target blob name.                                               | Required |
| `data`            | `bytes` \| `str`           | Data to upload. Strings are UTF-8 encoded before upload.        | Required |
| `overwrite`       | `bool`                     | Whether to overwrite existing blob.                             | `False`  |
| `content_type`    | `str` \| `None`            | MIME type for the blob. Auto-detected from `blob_name` if None. | `None`   |
| `metadata`        | `dict[str, str]` \| `None` | Custom metadata for the blob.                                   | `None`   |
| `max_concurrency` | `int`                      | Maximum concurrent connections for the upload.                  | `4`      |

##### Returns

| Type             | Description                                                            |
| ---------------- | ---------------------------------------------------------------------- |
| `dict[str, Any]` | Upload result containing ETag, last modified time, and other metadata. |

##### Exceptions

| Exception               | Description                         |
| ----------------------- | ----------------------------------- |
| `ResourceExistsError`   | Blob exists and overwrite is False. |
| `ResourceNotFoundError` | Container does not exist.           |
| `HttpResponseError`     | Azure service error occurred.       |

##### Example

```python
async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    # Upload text content
    result = await client.upload_blob(
        "documents",
        "readme.txt",
        "Hello, World!",
        metadata={"author": "user1", "version": "1.0"}
    )
    
    # Upload binary content
    with open("image.jpg", "rb") as file_data:
        await client.upload_blob(
            "images",
            "photo.jpg",
            file_data.read(),
            overwrite=True,
            content_type="image/jpeg",
            max_concurrency=8
        )
```

##### download_blob

```python
async def download_blob(
    container_name: str,
    blob_name: str
) -> bytes
```

Downloads blob content.

**Parameters:**
- `container_name` (str): Container name
- `blob_name` (str): Blob name

**Returns:** bytes - Blob content. Decode bytes in application code when text
is expected.

---

#### blob_exists

```python
async def blob_exists(
    self,
    container_name: str,
    blob_name: str
) -> bool
```

Checks if a blob exists in the specified container.

**Parameters:**

| Name             | Type  | Description                     | Default  |
| ---------------- | ----- | ------------------------------- | -------- |
| `container_name` | `str` | Name of the container to check. | Required |
| `blob_name`      | `str` | Name of the blob to check.      | Required |

**Returns:**

| Type   | Description                                   |
| ------ | --------------------------------------------- |
| `bool` | `True` if the blob exists, `False` otherwise. |

**Example:**

```python
async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    if await client.blob_exists("documents", "readme.txt"):
        print("Blob exists")
    else:
        print("Blob not found")
```

---

### SAS Token Operations

#### generate_blob_sas_url

```python
async def generate_blob_sas_url(
    self,
    container_name: str,
    blob_name: str,
    expiry_hours: int = 24,
    permissions: str = "r"
) -> str
```

Generates a Shared Access Signature (SAS) URL for secure blob access.

**Parameters:**

| Name             | Type  | Description                                                                   | Default  |
| ---------------- | ----- | ----------------------------------------------------------------------------- | -------- |
| `container_name` | `str` | Name of the container containing the blob.                                    | Required |
| `blob_name`      | `str` | Name of the blob to generate SAS for.                                         | Required |
| `expiry_hours`   | `int` | Number of hours until the SAS token expires.                                  | `24`     |
| `permissions`    | `str` | Permission string: `"r"` (read), `"w"` (write), `"d"` (delete), `"l"` (list). | `"r"`    |

**Returns:**

| Type  | Description                                               |
| ----- | --------------------------------------------------------- |
| `str` | Complete SAS URL with query parameters for secure access. |

**Permission Codes:**

| Code | Permission                             |
| ---- | -------------------------------------- |
| `r`  | Read the blob content and metadata     |
| `w`  | Write to the blob                      |
| `d`  | Delete the blob                        |
| `l`  | List operation (mainly for containers) |

**Example:**

```python
async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    # Generate read-only SAS URL valid for 2 hours
    _sas_url = await client.generate_blob_sas_url(
        "documents",
        "report.pdf",
        expiry_hours=2,
        permissions="r"
    )
    # SAS URLs are bearer tokens. Do not log, commit, or share the full URL.
    print("SAS URL generated; not displaying sensitive token.")
```

---

#### generate_container_sas_url

```python
async def generate_container_sas_url(
    self,
    container_name: str,
    expiry_hours: int = 24,
    permissions: str = "rl"
) -> str
```

Generates a Shared Access Signature (SAS) URL for secure container access.

**Parameters:**

| Name             | Type  | Description                                                 | Default  |
| ---------------- | ----- | ----------------------------------------------------------- | -------- |
| `container_name` | `str` | Name of the container to generate SAS for.                  | Required |
| `expiry_hours`   | `int` | Number of hours until the SAS token expires.                | `24`     |
| `permissions`    | `str` | Permission string. Use `"rl"` for read and list operations. | `"rl"`   |

**Returns:**

| Type  | Description                                                         |
| ----- | ------------------------------------------------------------------- |
| `str` | Complete SAS URL with query parameters for secure container access. |

**Note:** Container SAS tokens typically require `"rl"` permissions to list blobs within the container.

**Example:**

```python
async with AsyncStorageBlobHelper(account_name="myaccount") as client:
    # Generate container SAS URL for listing and reading
    _sas_url = await client.generate_container_sas_url(
        "documents",
        expiry_hours=6,
        permissions="rl"
    )
    # SAS URLs are bearer tokens. Do not log, commit, or share the full URL.
    print("Container SAS URL generated; not displaying sensitive token.")
```

---

### StorageBlobHelper

Synchronous client for Azure Blob Storage operations. It provides the same
core blob capabilities as `AsyncStorageBlobHelper`, but some parameters differ
to match the synchronous Azure SDK.

**Signature notes:** Do not assume async and sync signatures are identical. For
example, sync `upload_blob` accepts `content_settings` and `blob_tier`, while
async `upload_blob` accepts `content_type` and `max_concurrency`.

**Example:**

```python
from appfx.storage import StorageBlobHelper

client = StorageBlobHelper(account_name="myaccount")
client.create_container("documents")
client.upload_blob("documents", "file.txt", "Hello, World!")
content = client.download_blob("documents", "file.txt")
```

## Queue Storage Client

The queue storage client provides operations for managing queues and messages in Azure Storage. The library offers both asynchronous and synchronous implementations.

### AsyncStorageQueueHelper

Asynchronous client for Azure Queue Storage operations.

#### Constructor

```python
class AsyncStorageQueueHelper:
    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        credential: Optional[Any] = None,
        config: Optional[Union[dict[str, Any], Any]] = None
    ) -> None
```

Creates a new instance of the AsyncStorageQueueHelper.

**Parameters:**

| Name                | Type            | Description                                                          | Default  |
| ------------------- | --------------- | -------------------------------------------------------------------- | -------- |
| `connection_string` | `str` \| `None` | Complete Azure Storage connection string.                            | `None`   |
| `account_name`      | `str` \| `None` | Azure Storage account name. Required if not using connection_string. | `None`   |
| `credential`        | `Any` \| `None` | Azure credential object (DefaultAzureCredential, etc.).              | `None`   |
| `config`            | `dict[str, Any]` \| `Any` \| `None` | Configuration object or dictionary for custom settings. | `None` |

**Exceptions:**

| Exception             | Description                                                         |
| --------------------- | ------------------------------------------------------------------- |
| `ValueError`          | Raised when neither account_name nor connection_string is provided. |
| `ClientAuthenticationError` | Raised by the Azure SDK when authentication fails.          |

---

### Queue Operations

#### create_queue

```python
async def create_queue(
    self,
    queue_name: str,
    metadata: Optional[Dict[str, str]] = None
) -> bool
```

Creates a new queue in the storage account.

**Parameters:**

| Name         | Type                       | Description                                                      | Default  |
| ------------ | -------------------------- | ---------------------------------------------------------------- | -------- |
| `queue_name` | `str`                      | Name of the queue to create. Must be lowercase, 3-63 characters. | Required |
| `metadata`   | `Dict[str, str]` \| `None` | User-defined metadata as key-value pairs.                        | `None`   |

**Returns:**

| Type   | Description                                   |
| ------ | --------------------------------------------- |
| `bool` | `True` if the queue was created successfully. |

**Example:**

```python
from appfx.storage import AsyncStorageQueueHelper

async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    success = await client.create_queue("task-queue")
    print(f"Queue created: {success}")
```

---

#### delete_queue

```python
async def delete_queue(self, queue_name: str) -> bool
```

Deletes an existing queue and all its messages.

**Parameters:**

| Name         | Type  | Description                  | Default  |
| ------------ | ----- | ---------------------------- | -------- |
| `queue_name` | `str` | Name of the queue to delete. | Required |

**Returns:**

| Type   | Description                                   |
| ------ | --------------------------------------------- |
| `bool` | `True` if the queue was deleted successfully. |

**Example:**

```python
from appfx.storage import AsyncStorageQueueHelper

async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    success = await client.delete_queue("old-queue")
    print(f"Queue deleted: {success}")
```

---

#### list_queues

```python
async def list_queues(
    self,
    name_starts_with: Optional[str] = None,
    include_metadata: bool = False
) -> List[Dict[str, Any]]
```

Lists all queues in the storage account.

**Parameters:**

| Name               | Type            | Description                        | Default |
| ------------------ | --------------- | ---------------------------------- | ------- |
| `name_starts_with` | `str` \| `None` | Filter queues by name prefix.      | `None`  |
| `include_metadata` | `bool`          | Include queue metadata in results. | `False` |

**Returns:**

| Type              | Description                        |
| ----------------- | ---------------------------------- |
| `List[Dict[str, Any]]` | List of queue information dictionaries. |

**Example:**

```python
from appfx.storage import AsyncStorageQueueHelper

async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    # List all queues
    queues = await client.list_queues()
    
    # List queues with prefix and metadata
    task_queues = await client.list_queues(
        name_starts_with="task-",
        include_metadata=True
    )
    
    for queue in queues:
        print(f"Queue: {queue['name']}")
```

---

### Message Operations

#### send_message

```python
async def send_message(
    self,
    queue_name: str,
    content: str | bytes | dict | list,
    visibility_timeout: Optional[int] = None,
    time_to_live: Optional[int] = None
) -> dict[str, Any]
```

Sends a message to the specified queue.

**Parameters:**

| Name                 | Type            | Description                            | Default  |
| -------------------- | --------------- | -------------------------------------- | -------- |
| `queue_name`         | `str`           | Name of the target queue.              | Required |
| `content`            | `str` \| `bytes` \| `dict` \| `list` | Message content to send. Bytes are UTF-8 decoded; dictionaries and lists are JSON serialized. | Required |
| `visibility_timeout` | `int` \| `None` | Initial visibility timeout in seconds. | `None`   |
| `time_to_live`       | `int` \| `None` | Message time-to-live in seconds.       | `None`   |

**Returns:**

| Type                | Description                                       |
| ------------------- | ------------------------------------------------- |
| `dict[str, Any]` | Message information including `message_id`, `pop_receipt`, `inserted_on`, `expires_on`, and `next_visible_on`. |

**Example:**

```python
async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    result = await client.send_message(
        "task-queue",
        "Process file: document.pdf",
        time_to_live=3600
    )
    print(f"Message sent with ID: {result['message_id']}")
```

---

#### receive_messages

```python
async def receive_messages(
    self,
    queue_name: str,
    max_messages: int = 32,
    visibility_timeout: Optional[int] = None,
    timeout: Optional[int] = None
) -> list[dict[str, Any]]
```

Receives messages from the specified queue.

**Parameters:**

| Name                 | Type            | Description                                          | Default  |
| -------------------- | --------------- | ---------------------------------------------------- | -------- |
| `queue_name`         | `str`           | Name of the source queue.                            | Required |
| `max_messages`       | `int`           | Maximum number of messages to receive (1-32).        | `32`     |
| `visibility_timeout` | `int` \| `None` | Visibility timeout in seconds for received messages. | `None`   |
| `timeout`            | `int` \| `None` | Request timeout in seconds.                          | `None`   |

**Returns:**

| Type                 | Description                       |
| -------------------- | --------------------------------- |
| `List[dict[str, Any]]` | Received messages with `message_id`, `content`, `pop_receipt`, `inserted_on`, `expires_on`, `next_visible_on`, and `dequeue_count`. |

**Example:**

```python
async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    # Receive single message
    messages = await client.receive_messages("task-queue")
    
    # Receive multiple messages with custom visibility timeout
    batch_messages = await client.receive_messages(
        "task-queue",
        max_messages=10,
        visibility_timeout=300
    )
    
    for message in messages:
        print(f"Message: {message['content']}")
        # Process message here
        await client.delete_message("task-queue", message['message_id'], message['pop_receipt'])
```

---

#### peek_messages

```python
async def peek_messages(
    self,
    queue_name: str,
    max_messages: int = 32
) -> list[dict[str, Any]]
```

Peeks at messages from the queue without making them invisible.

**Parameters:**

| Name           | Type  | Description                                | Default  |
| -------------- | ----- | ------------------------------------------ | -------- |
| `queue_name`   | `str` | Name of the source queue.                  | Required |
| `max_messages` | `int` | Maximum number of messages to peek (1-32). | `32`     |

**Returns:**

| Type                 | Description                                            |
| -------------------- | ------------------------------------------------------ |
| `List[dict[str, Any]]` | Peeked messages with `message_id`, `content`, `inserted_on`, `expires_on`, and `next_visible_on`. Peeked messages do not include `pop_receipt`. |

**Example:**

```python
async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    # Peek at messages without removing them
    messages = await client.peek_messages("task-queue", max_messages=5)
    
    for message in messages:
        print(f"Peeked message: {message['content']}")
```

---

#### delete_message

```python
async def delete_message(
    self,
    queue_name: str,
    message_id: str,
    pop_receipt: str
) -> bool
```

Deletes a message from the queue using its ID and pop receipt.

**Parameters:**

| Name          | Type  | Description                                           | Default  |
| ------------- | ----- | ----------------------------------------------------- | -------- |
| `queue_name`  | `str` | Name of the queue containing the message.             | Required |
| `message_id`  | `str` | Unique identifier of the message to delete.           | Required |
| `pop_receipt` | `str` | Pop receipt obtained from receive_messages operation. | Required |

**Returns:**

| Type   | Description                                     |
| ------ | ----------------------------------------------- |
| `bool` | `True` if the message was deleted successfully. |

**Example:**

```python
async with AsyncStorageQueueHelper(account_name="myaccount") as client:
    # Receive and delete messages
    messages = await client.receive_messages("task-queue")
    
    for message in messages:
        # Process the message
        print(f"Processing: {message['content']}")
        
        # Delete after processing
        success = await client.delete_message(
            "task-queue",
            message['message_id'],
            message['pop_receipt']
        )
        print(f"Message deleted: {success}")
```

---

### StorageQueueHelper

Synchronous client for Azure Queue Storage operations. It provides the same core
queue capabilities as `AsyncStorageQueueHelper`, but sync methods include some
Azure SDK request-timeout parameters that async methods do not.

**Signature notes:** Do not assume async and sync signatures are identical. For
example, sync `send_message` uses a `message` parameter and optional `timeout`;
async `send_message` uses `content` and has no `timeout` parameter.

**Example:**

```python
from appfx.storage import StorageQueueHelper

client = StorageQueueHelper(account_name="myaccount")

# Synchronous operations
client.create_queue("task-queue")
client.send_message("task-queue", "Hello, World!")
messages = client.receive_messages("task-queue")
```

## Configuration

### Connection Methods

The Azure Storage Helper Library supports multiple authentication methods:

#### Azure Default Credential (Recommended)

```python
from appfx.storage import AsyncStorageBlobHelper, StorageBlobHelper
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

# Async client
async_client = AsyncStorageBlobHelper(
    account_name="mystorageaccount",
    credential=AsyncDefaultAzureCredential()
)

# Sync client
sync_client = StorageBlobHelper(
    account_name="mystorageaccount", 
    credential=DefaultAzureCredential()
)
```

#### Connection String

Connection strings are supported for compatibility, but public examples avoid
showing connection-string structure. Prefer account-name authentication with
managed identity or Azure CLI credentials for new code.

#### Account Name with Managed Identity

```python
import os

from appfx.storage import AsyncStorageBlobHelper


client = AsyncStorageBlobHelper(
    account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
)
```

---

### Configuration Class

#### StorageConfig

Base configuration class for storage helper initialization.

```python
class StorageConfig:
    def __init__(
        self,
        config_dict: Optional[dict[str, Any]] = None
    ) -> None
```

**Parameters:**

| Name          | Type                         | Description                                   | Default |
| ------------- | ---------------------------- | --------------------------------------------- | ------- |
| `config_dict` | `dict[str, Any]` \| `None`   | Optional configuration overrides.             | `None`  |

---

## Exceptions

### Exception Hierarchy

The library uses Azure SDK exceptions with additional context and validation:

#### Azure SDK Exceptions

| Exception                   | Description                        | When Raised                                 |
| --------------------------- | ---------------------------------- | ------------------------------------------- |
| `ResourceNotFoundError`     | Requested resource does not exist. | Container, blob, or queue not found.        |
| `ResourceExistsError`       | Resource already exists.           | Creating duplicate container or queue.      |
| `HttpResponseError`         | General Azure service error.       | Authentication, network, or service issues. |
| `ClientAuthenticationError` | Authentication failed.             | Invalid credentials or permissions.         |

#### Validation Exceptions

| Exception    | Description                  | When Raised                                  |
| ------------ | ---------------------------- | -------------------------------------------- |
| `ValueError` | Invalid parameters provided. | Invalid names, configurations, or arguments. |
| `TypeError`  | Incorrect parameter type.    | Wrong data types passed to methods.          |

### Error Handling Example

```python
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

try:
    async with AsyncStorageBlobHelper(account_name="myaccount") as client:
        await client.upload_blob("container", "blob.txt", "data")
        
except ResourceNotFoundError:
    print("Container does not exist")
    
except HttpResponseError as e:
    print(f"Azure service error: {e.status_code} - {e.message}")
    
except ValueError as e:
    print(f"Invalid parameter: {e}")
```

### Error Response Format
The helpers propagate Azure SDK exceptions rather than wrapping them in a
custom error envelope. Catch Azure exceptions such as `ResourceNotFoundError`,
`ResourceExistsError`, `HttpResponseError`, and `ClientAuthenticationError`
where callers need custom recovery or user-facing messages.

## Type Definitions

---

## Data Models

### Type Definitions

The library uses strongly-typed models for consistent data handling:

```python
from typing import Union, Dict, List, Any, Optional
from datetime import datetime

# Content types for upload operations
ContentData = Union[str, bytes]

# Metadata dictionary for custom properties
Metadata = Dict[str, str]

# Blob information returned by list operations
BlobInfo = Dict[str, Any]

# Container information returned by list operations  
ContainerInfo = Dict[str, Any]

# Queue information returned by list operations
QueueInfo = Dict[str, Any]

# Message information returned by queue operations
QueueMessage = Dict[str, Any]

# Message send result information
MessageSendResult = Dict[str, Any]
```

### Permission Constants

#### Blob Storage Permissions

| Permission | Code | Description                               |
| ---------- | ---- | ----------------------------------------- |
| Read       | `r`  | Read blob content and metadata            |
| Write      | `w`  | Write or update blob content              |
| Delete     | `d`  | Delete the blob                           |
| List       | `l`  | List operation (primarily for containers) |

#### Container Storage Permissions

| Permission | Code | Description                                 |
| ---------- | ---- | ------------------------------------------- |
| Read       | `r`  | Read blob content, metadata, and properties |
| List       | `l`  | List blobs within the container             |
| Write      | `w`  | Write blob content and metadata             |
| Delete     | `d`  | Delete blobs within the container           |

### Storage Tier Options

Azure Blob Storage offers different access tiers for cost optimization:

| Tier    | Code      | Use Case                   | Access Pattern                                        |
| ------- | --------- | -------------------------- | ----------------------------------------------------- |
| Hot     | `Hot`     | Frequently accessed data   | Immediate access, higher storage cost                 |
| Cool    | `Cool`    | Infrequently accessed data | 30+ day retention, lower storage cost                 |
| Archive | `Archive` | Rarely accessed data       | 180+ day retention, lowest cost, rehydration required |

---

## Examples

### Blob Storage Workflow

Complete example demonstrating blob storage operations:

```python
import os

from appfx.storage import AsyncStorageBlobHelper

async def comprehensive_blob_example():
    """Demonstrates complete blob storage workflow."""
    
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]

    # Initialize client with DefaultAzureCredential by account name.
    async with AsyncStorageBlobHelper(
        account_name=account_name,
    ) as client:
        
        container_name = "documents"
        blob_name = "report.pdf"
        
        try:
            # 1. Create container if it doesn't exist
            if not await client.container_exists(container_name):
                await client.create_container(
                    container_name,
                    metadata={"purpose": "document-storage", "owner": "finance-team"}
                )
                print(f"Created container: {container_name}")
            
            # 2. Upload blob with metadata
            with open("local_report.pdf", "rb") as file_data:
                upload_result = await client.upload_blob(
                    container_name,
                    blob_name,
                    file_data.read(),
                    overwrite=True,
                    content_type="application/pdf",
                    metadata={"document_type": "financial_report", "quarter": "Q1"}
                )
                print(f"Uploaded blob: {upload_result['etag']}")
            
            # 3. Generate time-limited SAS URL for secure sharing
            _sas_url = await client.generate_blob_sas_url(
                container_name,
                blob_name,
                expiry_hours=24,  # Valid for 24 hours
                permissions="r"   # Read-only access
            )
            # SAS URLs are bearer tokens. Do not log, commit, or share the full URL.
            print("Generated SAS URL; not displaying sensitive token.")
            
            # 4. List all blobs in container
            blobs = await client.list_blobs(
                container_name,
                include_metadata=True,
            )
            
            for blob in blobs:
                print(f"Found blob: {blob['name']} ({blob['size']} bytes)")
            
            # 5. Download and verify content
            if await client.blob_exists(container_name, blob_name):
                downloaded_content = await client.download_blob(
                    container_name,
                    blob_name,
                )
                
                # Save to local file
                with open("downloaded_report.pdf", "wb") as output_file:
                    output_file.write(downloaded_content)
                print("Downloaded and saved blob content")
            
        except Exception as e:
            print(f"Error in blob workflow: {e}")
            
        finally:
            # Optional: Cleanup (uncomment if needed)
            # await client.delete_blob(container_name, blob_name)
            # await client.delete_container(container_name)
            pass

# Run the example
import asyncio
asyncio.run(comprehensive_blob_example())
```

### Queue Storage Workflow

Complete example demonstrating queue storage operations:

```python
import asyncio
import os

from appfx.storage import AsyncStorageQueueHelper

async def comprehensive_queue_example():
    """Demonstrates complete queue storage workflow."""
    
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]

    # Initialize client with DefaultAzureCredential by account name.
    async with AsyncStorageQueueHelper(
        account_name=account_name,
    ) as client:
        
        queue_name = "processing-tasks"
        
        try:
            # 1. Create queue for task processing
            await client.create_queue(
                queue_name,
                metadata={"purpose": "background-processing", "team": "data-engineering"}
            )
            print(f"Created queue: {queue_name}")
            
            # 2. Send multiple task messages
            tasks = [
                {"task_type": "data_processing", "file_path": "/data/file1.csv"},
                {"task_type": "report_generation", "template": "monthly_report"},
                {"task_type": "data_validation", "schema": "user_data_v2"}
            ]
            
            for task in tasks:
                result = await client.send_message(
                    queue_name,
                    task,
                    time_to_live=3600  # Message expires in 1 hour
                )
                print(f"Sent task message: {result['message_id']}")
            
            # 3. Peek at messages without processing
            peeked_messages = await client.peek_messages(queue_name, max_messages=5)
            print(f"Found {len(peeked_messages)} messages in queue")
            
            # 4. Process messages with proper error handling
            processed_count = 0
            max_messages_to_process = 10
            
            while processed_count < max_messages_to_process:
                # Receive messages with 5-minute visibility timeout
                messages = await client.receive_messages(
                    queue_name,
                    max_messages=5,
                    visibility_timeout=300
                )
                
                if not messages:
                    print("No more messages to process")
                    break
                
                for message in messages:
                    try:
                        # Parse task from message content
                        task = message['content']
                        print(f"Processing task: {task['task_type']}")
                        
                        # Simulate task processing
                        await asyncio.sleep(1)  # Simulated work
                        
                        # Delete message after successful processing
                        await client.delete_message(
                            queue_name,
                            message['message_id'],
                            message['pop_receipt']
                        )
                        
                        processed_count += 1
                        print(f"Completed task {processed_count}")
                        
                    except Exception as e:
                        print(f"Error processing message {message['message_id']}: {e}")
                        # Message will become visible again after timeout
                        # Implement dead letter handling in production
            
            print(f"Processing complete. Handled {processed_count} messages.")
            
        except Exception as e:
            print(f"Error in queue workflow: {e}")
            
        finally:
            # Optional: Cleanup (uncomment if needed)
            # await client.delete_queue(queue_name)
            pass

# Run the example
asyncio.run(comprehensive_queue_example())
```
