"""
Add metadata to blobs - key-value pairs made easy!
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
        # Upload with metadata
        metadata = {
            "author": "John Doe",
            "department": "Engineering",
            "project": "StorageHelper",
        }

        await helper.upload_blob(
            container_name="appfx-demo-container",
            blob_name="report.pdf",
            data=b"PDF content here...",
            metadata=metadata,
            overwrite=True,
        )

        # Read metadata back
        properties = await helper.get_blob_properties(
            "appfx-demo-container", "report.pdf"
        )
        print("Metadata:")
        for key, value in properties["metadata"].items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
