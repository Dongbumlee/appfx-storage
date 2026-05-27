"""
Send JSON objects as messages - automatic serialization!
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
        # Send structured data as JSON
        user_data = {
            "user_id": 12345,
            "action": "login",
            "timestamp": "2025-09-18T10:30:00Z",
            "ip_address": "192.168.1.100",
        }
        await helper.create_queue("appfx-events")
        await helper.send_message("appfx-events", user_data)
        print("JSON message sent!")

        # Receive and parse JSON automatically
        message = await helper.receive_message("appfx-events")
        if message:
            content = message["content"]  # Already parsed as dict
            print(f"User {content['user_id']} performed {content['action']}")
            await helper.delete_message(
                "appfx-events", message["message_id"], message["pop_receipt"]
            )


if __name__ == "__main__":
    asyncio.run(main())
