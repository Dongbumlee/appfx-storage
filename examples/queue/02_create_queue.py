"""
Create queues automatically - just like containers!
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
        # Create queue (handles "if not exists" automatically)
        created = await helper.create_queue("appfx-new-queue")
        if created:
            print("Queue created successfully!")
        else:
            print("Queue already exists - ready to use!")

        # Send first message to the new queue
        await helper.send_message("appfx-new-queue", "First message in new queue!")
        print("Message sent to new queue!")


if __name__ == "__main__":
    asyncio.run(main())
