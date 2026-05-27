"""
Batch operations - send multiple messages at once!
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
        # Send multiple messages concurrently
        messages = [
            "Task 1: Process order #1001",
            "Task 2: Send welcome email",
            "Task 3: Update inventory",
            {"task_id": 4, "action": "backup_database", "priority": "high"},
        ]

        await helper.create_queue("appfx-tasks")
        results = await helper.send_messages_batch("appfx-tasks", messages)
        print(f"Sent {len(results)} messages concurrently!")

        # Receive multiple messages at once
        received_messages = await helper.receive_messages("appfx-tasks", max_messages=3)
        print(f"Received {len(received_messages)} messages:")

        for message in received_messages:
            print(f"  - {message['content']}")
            # Process and delete each message
            await helper.delete_message(
                "appfx-tasks", message["message_id"], message["pop_receipt"]
            )


if __name__ == "__main__":
    asyncio.run(main())
