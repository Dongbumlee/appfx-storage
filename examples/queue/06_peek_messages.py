"""
Peek at messages without removing them from queue!
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
        # Send some messages first
        await helper.create_queue("peek-demo")
        messages = ["Message 1", "Message 2", "Message 3"]
        await helper.send_messages_batch("peek-demo", messages)

        # Peek at messages without removing them
        peeked = await helper.peek_messages("peek-demo", max_messages=5)
        print(f"Peeked at {len(peeked)} messages:")
        for i, message in enumerate(peeked, 1):
            print(f"  {i}. {message['content']}")

        print("\nMessages are still in the queue!")

        # Now actually receive and process them
        while True:
            message = await helper.receive_message("peek-demo")
            if not message:
                break

            print(f"Processing: {message['content']}")
            await helper.delete_message(
                "peek-demo", message["message_id"], message["pop_receipt"]
            )

        print("All messages processed!")


if __name__ == "__main__":
    asyncio.run(main())
