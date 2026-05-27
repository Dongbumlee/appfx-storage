"""
Queue management - list, properties, and cleanup!
"""

import asyncio
import os

from appfx.storage import AsyncStorageQueueHelper


def require_account_name() -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_NAME before running this live Azure example."
        )
    return account_name


async def main():
    async with AsyncStorageQueueHelper(account_name=require_account_name()) as helper:
        # List all queues in the account
        queues = await helper.list_queues()
        print(f"Found {len(queues)} queues:")
        for queue in queues:
            print(f"  📋 {queue['name']}")

        # Get properties of a specific queue
        if queues:
            queue_name = queues[0]["name"]
            properties = await helper.get_queue_properties(queue_name)
            print(f"\nQueue '{queue_name}' properties:")
            print(f"  Messages: {properties.get('approximate_message_count', 0)}")
            print(f"  Metadata: {properties.get('metadata', {})}")

        # Set custom metadata on an isolated demo queue.
        await helper.create_queue("appfx-metadata-demo")
        await helper.set_queue_metadata(
            "appfx-metadata-demo",
            {
                "purpose": "user_notifications",
                "environment": "example",
                "created_by": "StorageHelper",
            },
        )
        print("Metadata set on queue!")

        # Check if queue exists
        exists = await helper.queue_exists("nonexistent-queue")
        print(f"Queue 'nonexistent-queue' exists: {exists}")


if __name__ == "__main__":
    asyncio.run(main())
