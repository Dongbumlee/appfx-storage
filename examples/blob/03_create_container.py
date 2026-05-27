"""
Create containers if they don't exist - one simple call!
"""

import asyncio
import os

from appfx.storage import AsyncStorageBlobHelper


def require_account_name() -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_NAME before running this live Azure example."
        )
    return account_name


async def main():
    async with AsyncStorageBlobHelper(account_name=require_account_name()) as helper:
        # Create container (only if it doesn't exist)
        created = await helper.create_container("appfx-new-container")
        if created:
            print("Container created successfully!")
        else:
            print("Container already exists - ready to use!")

        # Now upload something
        await helper.upload_blob(
            "appfx-new-container",
            "test.txt",
            "Container created and ready!",
            overwrite=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
