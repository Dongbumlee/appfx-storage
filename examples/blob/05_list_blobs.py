"""
List all blobs in a container - simple iteration!
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
        # List all blobs - returns list of blob info
        print("Files in container 'mycontainer':")
        blobs = await helper.list_blobs("appfx-demo-container")
        for blob in blobs:
            size_mb = blob["size"] / (1024 * 1024)
            print(f"  📄 {blob['name']} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
