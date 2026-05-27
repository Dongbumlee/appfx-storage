"""
Message visibility and processing - control when messages reappear!
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
        # Send a message that needs time to process
        await helper.create_queue("processing")
        await helper.send_message("processing", "Long running task")

        # Receive with custom visibility timeout (30 seconds)
        message = await helper.receive_message(
            queue_name="processing",
            visibility_timeout=30,  # Message invisible for 30 seconds
        )

        if message:
            print(f"Processing: {message['content']}")
            print("Message will be invisible for 30 seconds...")

            # Simulate processing time
            await asyncio.sleep(2)

            # Update the message (extend processing time if needed)
            update_result = await helper.update_message(
                queue_name="processing",
                message_id=message["message_id"],
                pop_receipt=message["pop_receipt"],
                content="Updated: Processing 50% complete",
                visibility_timeout=60,  # Extend to 60 seconds
            )
            print("Message updated and visibility extended!")

            # Complete processing and delete using the NEW pop_receipt
            await helper.delete_message(
                "processing", message["message_id"], update_result["pop_receipt"]
            )
            print("Task completed and message deleted!")


if __name__ == "__main__":
    asyncio.run(main())
