#!/usr/bin/env python3
"""
Asynchronous Azure Storage Queue Helper

This module provides an asynchronous version of the StorageQueueHelper class
for high-performance, non-blocking queue operations.
"""

import asyncio
import json
import logging
from typing import Any

from azure.core.exceptions import (
    ResourceExistsError,
    ResourceNotFoundError,
)
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueServiceClient

from ..shared_config import get_config

QueueMessageContent = str | bytes | dict[str, Any] | list[Any]


class AsyncStorageQueueHelper:
    """
    Asynchronous Azure Storage Queue Helper Class

    Provides high-performance, non-blocking operations for Azure Queue Storage
    with support for concurrent message processing and batch operations.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        account_name: str | None = None,
        credential: Any | None = None,
        config: dict | Any | None = None,
    ):
        """
        Initialize the AsyncStorageQueueHelper

        Args:
            connection_string: Azure Storage connection string (preferred for development)
            account_name: Storage account name (for managed identity)
            credential: Azure credential (DefaultAzureCredential for production)
            config: Configuration object or dictionary for custom settings
        """
        self.config: Any
        # Set up configuration
        if config:
            if isinstance(config, dict):
                self.config = config
            else:
                self.config = config
        else:
            self.config = get_config()

        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, self.config.get("logging_level", "ERROR"))
        )

        # Suppress Azure SDK logging to reduce noise
        azure_loggers = [
            "azure.storage.queue",
            "azure.storage.queue.aio",
            "azure.core.pipeline",
            "azure.core.pipeline.policies",
            "azure.identity",
            "azure.identity.aio",
            "urllib3.connectionpool",
            "azure.core.pipeline.policies.http_logging_policy",
        ]
        for logger_name in azure_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        self._connection_string = connection_string
        self._account_name = account_name
        self._credential = credential
        self._queue_service_client = None

    @staticmethod
    def _serialize_message_content(content: QueueMessageContent) -> str:
        """Convert supported queue message content to the SDK's expected string."""
        if isinstance(content, (dict, list)):
            return json.dumps(content)
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return str(content)

    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _initialize_client(self):
        """Initialize the async queue service client"""
        try:
            if self._connection_string:
                self._queue_service_client = QueueServiceClient.from_connection_string(
                    self._connection_string
                )
            elif self._account_name and self._credential:
                account_url = f"https://{self._account_name}.queue.core.windows.net"
                self._queue_service_client = QueueServiceClient(
                    account_url, credential=self._credential
                )
            elif self._account_name:
                # Use DefaultAzureCredential for managed identity
                account_url = f"https://{self._account_name}.queue.core.windows.net"
                self._queue_service_client = QueueServiceClient(
                    account_url, credential=DefaultAzureCredential()
                )
            else:
                raise ValueError(
                    "Either connection_string or account_name must be provided"
                )

        except Exception as e:
            self.logger.error(f"Failed to initialize QueueServiceClient: {e}")
            raise

    async def close(self):
        """Close the queue service client and all associated resources"""
        if self._queue_service_client:
            try:
                # Close the queue service client first
                await self._queue_service_client.close()

                # If using Azure identity credentials, close their HTTP sessions too
                if (
                    hasattr(self._queue_service_client, "credential")
                    and self._queue_service_client.credential
                ):
                    credential = self._queue_service_client.credential

                    # Close DefaultAzureCredential and its chained credentials
                    if hasattr(credential, "close"):
                        try:
                            await credential.close()
                            self.logger.debug(
                                "Successfully closed credential HTTP sessions"
                            )
                        except Exception as e:
                            self.logger.debug(f"Error closing credential: {e}")

                    # For chained credentials (like DefaultAzureCredential), close each individual credential
                    if hasattr(credential, "_credentials"):
                        for cred in credential._credentials:
                            if hasattr(cred, "close"):
                                try:
                                    await cred.close()
                                except Exception as e:
                                    self.logger.debug(
                                        f"Error closing chained credential: {e}"
                                    )

            except Exception as e:
                self.logger.debug(f"Error during queue service client cleanup: {e}")
            finally:
                self._queue_service_client = None

    @property
    def queue_service_client(self):
        """Get the queue service client, initializing if needed"""
        if self._queue_service_client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with AsyncStorageQueueHelper(...) as helper:' or call await helper._initialize_client()"
            )
        return self._queue_service_client

    # Queue Operations
    async def create_queue(
        self, queue_name: str, metadata: dict[str, str] | None = None
    ) -> bool:
        """
        Create a new queue asynchronously

        Args:
            queue_name: Name of the queue
            metadata: Optional metadata dictionary

        Returns:
            bool: True if created successfully, False if already exists
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.create_queue(metadata=metadata)
            self.logger.info(f"Queue '{queue_name}' created successfully")
            return True
        except ResourceExistsError:
            self.logger.warning(f"Queue '{queue_name}' already exists")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create queue '{queue_name}': {e}")
            raise

    async def delete_queue(self, queue_name: str) -> bool:
        """
        Delete a queue asynchronously

        Args:
            queue_name: Name of the queue to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.delete_queue()
            self.logger.info(f"Queue '{queue_name}' deleted successfully")
            return True
        except ResourceNotFoundError:
            self.logger.warning(f"Queue '{queue_name}' not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete queue '{queue_name}': {e}")
            raise

    async def queue_exists(self, queue_name: str) -> bool:
        """
        Check if a queue exists asynchronously

        Args:
            queue_name: Name of the queue

        Returns:
            bool: True if queue exists
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.get_queue_properties()
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error checking queue existence: {e}")
            raise

    async def list_queues(
        self, name_starts_with: str | None = None, include_metadata: bool = False
    ) -> list[dict[str, Any]]:
        """
        List all queues asynchronously

        Args:
            name_starts_with: Filter queues by name prefix
            include_metadata: Include queue metadata

        Returns:
            List[Dict]: List of queue information
        """
        try:
            queues = []
            async for queue in self.queue_service_client.list_queues(
                name_starts_with=name_starts_with,
                include_metadata=include_metadata,
            ):
                queue_info: dict[str, Any] = {"name": queue.name}
                if include_metadata and queue.metadata:
                    queue_info["metadata"] = queue.metadata
                queues.append(queue_info)
            return queues
        except Exception as e:
            self.logger.error(f"Failed to list queues: {e}")
            raise

    # Message Operations
    async def send_message(
        self,
        queue_name: str,
        content: QueueMessageContent,
        visibility_timeout: int | None = None,
        time_to_live: int | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to a queue asynchronously

        Args:
            queue_name: Name of the queue
            content: Message content (string, UTF-8 bytes, dict, or list)
            visibility_timeout: Time in seconds the message is invisible after being retrieved
            time_to_live: Time in seconds the message lives in the queue

        Returns:
            Dict: Message information including message_id and pop_receipt
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)

            content = self._serialize_message_content(content)

            message = await queue_client.send_message(
                content,
                visibility_timeout=visibility_timeout,
                time_to_live=time_to_live,
            )

            self.logger.info(f"Message sent to queue '{queue_name}'")
            return {
                "message_id": message.id,
                "pop_receipt": message.pop_receipt,
                "inserted_on": message.inserted_on if message.inserted_on else None,
                "expires_on": message.expires_on if message.expires_on else None,
                "next_visible_on": message.next_visible_on
                if message.next_visible_on
                else None,
            }
        except Exception as e:
            self.logger.error(f"Failed to send message to queue '{queue_name}': {e}")
            raise

    async def receive_message(
        self,
        queue_name: str,
        visibility_timeout: int | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Receive a single message from a queue asynchronously

        Args:
            queue_name: Name of the queue
            visibility_timeout: Time in seconds the message is invisible after being retrieved
            timeout: Timeout in seconds for the operation

        Returns:
            Optional[Dict]: Message information or None if no message available
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)

            messages = []
            async for message in queue_client.receive_messages(
                max_messages=1,
                visibility_timeout=visibility_timeout,
                timeout=timeout,
            ):
                messages.append(message)
                break

            if not messages:
                return None

            message = messages[0]

            # Try to parse JSON content automatically
            content = message.content
            try:
                # Attempt to parse as JSON if it looks like JSON
                if isinstance(content, str) and content.strip().startswith(("{", "[")):
                    content = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, keep as string
                pass

            return {
                "message_id": message.id,
                "content": content,
                "pop_receipt": message.pop_receipt,
                "inserted_on": message.inserted_on,
                "expires_on": message.expires_on,
                "next_visible_on": message.next_visible_on,
                "dequeue_count": message.dequeue_count,
            }
        except Exception as e:
            self.logger.error(
                f"Failed to receive message from queue '{queue_name}': {e}"
            )
            raise

    async def receive_messages(
        self,
        queue_name: str,
        max_messages: int = 32,
        visibility_timeout: int | None = None,
        timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Receive multiple messages from a queue asynchronously

        Args:
            queue_name: Name of the queue
            max_messages: Maximum number of messages to retrieve (1-32)
            visibility_timeout: Time in seconds the message is invisible after being retrieved
            timeout: Timeout in seconds for the operation

        Returns:
            List[Dict]: List of message information
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)

            messages = []
            async for message in queue_client.receive_messages(
                max_messages=max_messages,
                visibility_timeout=visibility_timeout,
                timeout=timeout,
            ):
                # Try to parse JSON content automatically
                content = message.content
                try:
                    # Attempt to parse as JSON if it looks like JSON
                    if isinstance(content, str) and content.strip().startswith(
                        ("{", "[")
                    ):
                        content = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, keep as string
                    pass

                messages.append(
                    {
                        "message_id": message.id,
                        "content": content,
                        "pop_receipt": message.pop_receipt,
                        "inserted_on": message.inserted_on,
                        "expires_on": message.expires_on,
                        "next_visible_on": message.next_visible_on,
                        "dequeue_count": message.dequeue_count,
                    }
                )

            self.logger.info(
                f"Received {len(messages)} messages from queue '{queue_name}'"
            )
            return messages
        except Exception as e:
            self.logger.error(
                f"Failed to receive messages from queue '{queue_name}': {e}"
            )
            raise

    async def delete_message(
        self, queue_name: str, message_id: str, pop_receipt: str
    ) -> bool:
        """
        Delete a message from a queue asynchronously

        Args:
            queue_name: Name of the queue
            message_id: ID of the message to delete
            pop_receipt: Pop receipt of the message

        Returns:
            bool: True if deleted successfully
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.delete_message(message_id, pop_receipt)
            self.logger.info(f"Message {message_id} deleted from queue '{queue_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete message {message_id}: {e}")
            raise

    async def update_message(
        self,
        queue_name: str,
        message_id: str,
        pop_receipt: str,
        content: QueueMessageContent,
        visibility_timeout: int = 0,
    ) -> dict[str, Any]:
        """
        Update a message in a queue asynchronously

        Args:
            queue_name: Name of the queue
            message_id: ID of the message to update
            pop_receipt: Pop receipt of the message
            content: New content for the message (string, UTF-8 bytes, dict, or list)
            visibility_timeout: Time in seconds the message is invisible

        Returns:
            Dict: Updated message information
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)

            content = self._serialize_message_content(content)

            result = await queue_client.update_message(
                message_id,
                pop_receipt=pop_receipt,
                content=content,
                visibility_timeout=visibility_timeout,
            )

            self.logger.info(f"Message {message_id} updated in queue '{queue_name}'")
            return {
                "pop_receipt": result.pop_receipt,
                "next_visible_on": result.next_visible_on,
            }
        except Exception as e:
            self.logger.error(f"Failed to update message {message_id}: {e}")
            raise

    # Batch Operations
    async def send_messages_batch(
        self,
        queue_name: str,
        messages: list[QueueMessageContent],
        max_concurrency: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Send multiple messages concurrently

        Args:
            queue_name: Name of the queue
            messages: List of message contents
            max_concurrency: Maximum concurrent operations

        Returns:
            List[Dict]: List of sent message information
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def send_single_message(content: QueueMessageContent) -> dict[str, Any]:
            async with semaphore:
                return await self.send_message(queue_name, content)

        # Execute sends concurrently
        tasks = [send_single_message(content) for content in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        sent_messages: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                self.logger.error(f"Failed to send message {i}: {result}")
            else:
                sent_messages.append(result)

        return sent_messages

    async def process_messages_batch(
        self,
        queue_name: str,
        processor_func,
        max_messages: int = 32,
        max_concurrency: int = 10,
        delete_after_processing: bool = True,
        visibility_timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Process multiple messages concurrently

        Args:
            queue_name: Name of the queue
            processor_func: Async function to process each message
            max_messages: Maximum number of messages to retrieve
            max_concurrency: Maximum concurrent processing
            delete_after_processing: Whether to delete messages after successful processing
            visibility_timeout: Time in seconds the message is invisible

        Returns:
            List[Dict]: List of processing results
        """
        # Receive messages
        messages = await self.receive_messages(
            queue_name,
            max_messages=max_messages,
            visibility_timeout=visibility_timeout,
        )

        if not messages:
            return []

        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_single_message(message: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                try:
                    # Process the message
                    result = await processor_func(message)

                    # Delete message if processing succeeded and delete_after_processing is True
                    if delete_after_processing:
                        await self.delete_message(
                            queue_name, message["message_id"], message["pop_receipt"]
                        )

                    return {
                        "message_id": message["message_id"],
                        "success": True,
                        "result": result,
                    }
                except Exception as e:
                    self.logger.error(
                        f"Failed to process message {message['message_id']}: {e}"
                    )
                    return {
                        "message_id": message["message_id"],
                        "success": False,
                        "error": str(e),
                    }

        # Execute processing concurrently
        tasks = [process_single_message(message) for message in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        processed_results: list[dict[str, Any]] = []
        for result in results:
            if not isinstance(result, BaseException):
                processed_results.append(result)

        return processed_results

    # Utility Methods
    async def get_queue_properties(self, queue_name: str) -> dict[str, Any]:
        """
        Get queue properties asynchronously

        Args:
            queue_name: Name of the queue

        Returns:
            Dict: Queue properties
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            properties = await queue_client.get_queue_properties()

            return {
                "name": queue_name,
                "metadata": properties.metadata or {},
                "approximate_message_count": properties.approximate_message_count,
            }
        except Exception as e:
            self.logger.error(f"Failed to get queue properties: {e}")
            raise

    async def set_queue_metadata(
        self, queue_name: str, metadata: dict[str, str]
    ) -> bool:
        """
        Set queue metadata asynchronously

        Args:
            queue_name: Name of the queue
            metadata: Metadata dictionary

        Returns:
            bool: True if metadata set successfully
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.set_queue_metadata(metadata)
            self.logger.info(f"Metadata set for queue '{queue_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set queue metadata: {e}")
            raise

    async def clear_queue(self, queue_name: str) -> bool:
        """
        Clear all messages from a queue asynchronously

        Args:
            queue_name: Name of the queue

        Returns:
            bool: True if cleared successfully
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)
            await queue_client.clear_messages()
            self.logger.info(f"Queue '{queue_name}' cleared successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear queue '{queue_name}': {e}")
            raise

    async def peek_messages(
        self, queue_name: str, max_messages: int = 32
    ) -> list[dict[str, Any]]:
        """
        Peek at messages in a queue without removing them asynchronously

        Args:
            queue_name: Name of the queue
            max_messages: Maximum number of messages to peek (1-32)

        Returns:
            List[Dict]: List of message information
        """
        try:
            queue_client = self.queue_service_client.get_queue_client(queue_name)

            messages = []
            peek_messages = await queue_client.peek_messages(max_messages=max_messages)
            for message in peek_messages:
                # Try to parse JSON content automatically
                content = message.content
                try:
                    # Attempt to parse as JSON if it looks like JSON
                    if isinstance(content, str) and content.strip().startswith(
                        ("{", "[")
                    ):
                        content = json.loads(content)
                except (json.JSONDecodeError, ValueError):
                    # If parsing fails, keep as string
                    pass

                messages.append(
                    {
                        "message_id": message.id,
                        "content": content,
                        "inserted_on": message.inserted_on,
                        "expires_on": message.expires_on,
                        "next_visible_on": message.next_visible_on,
                    }
                )

            return messages
        except Exception as e:
            self.logger.error(f"Failed to peek messages from queue '{queue_name}': {e}")
            raise
