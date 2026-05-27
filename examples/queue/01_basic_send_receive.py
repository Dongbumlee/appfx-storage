"""
Basic Queue Operations - Send and receive messages in 3 lines!
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
        # if not queue exists create
        await helper.create_queue("appfx-demo-queue")

        # Send a message
        await helper.send_message("appfx-demo-queue", "Hello, Queue!")

        # Receive and process the message
        message = await helper.receive_message("appfx-demo-queue")
        if message:
            print(f"Received: {message['content']}")
            # Delete the message after processing
            await helper.delete_message(
                "appfx-demo-queue", message["message_id"], message["pop_receipt"]
            )


if __name__ == "__main__":
    asyncio.run(main())
