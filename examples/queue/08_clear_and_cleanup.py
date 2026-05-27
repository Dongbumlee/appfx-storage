"""
Clear queue and cleanup operations!
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
        # Send some test messages
        await helper.create_queue("cleanup-demo")
        test_messages = ["Test 1", "Test 2", "Test 3"]
        await helper.send_messages_batch("cleanup-demo", test_messages)
        print("Added test messages to queue")

        # Check queue status
        properties = await helper.get_queue_properties("cleanup-demo")
        msg_count = properties.get("approximate_message_count", 0)
        print(f"Queue has approximately {msg_count} messages")

        # Clear all messages from queue (faster than deleting one by one)
        cleared = await helper.clear_queue("cleanup-demo")
        if cleared:
            print("Queue cleared successfully!")

        # Verify queue is empty
        properties = await helper.get_queue_properties("cleanup-demo")
        msg_count = properties.get("approximate_message_count", 0)
        print(f"Queue now has {msg_count} messages")

        # Delete the entire queue if no longer needed
        # deleted = await helper.delete_queue("cleanup-demo")
        # print(f"Queue deleted: {deleted}")


if __name__ == "__main__":
    asyncio.run(main())
