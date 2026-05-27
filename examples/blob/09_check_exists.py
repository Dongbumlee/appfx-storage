"""
Check if blob exists - quick and simple!
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
        blob_name = "file1.txt"

        # Check existence before operations
        if await helper.blob_exists("appfx-demo-container", blob_name):
            print(f"✅ {blob_name} exists - downloading...")
            content = await helper.download_blob("appfx-demo-container", blob_name)
            print(f"Content: {content.decode()}")
        else:
            print(f"❌ {blob_name} doesn't exist - creating...")
            await helper.upload_blob(
                "appfx-demo-container", blob_name, "New file content!"
            )
            print("File created!")


if __name__ == "__main__":
    asyncio.run(main())
