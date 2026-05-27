"""
Upload any file - just point to the file path!
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


def require_sample_file_path() -> str:
    file_path = os.environ.get("AZURE_STORAGE_SAMPLE_FILE")
    if not file_path:
        raise RuntimeError(
            "Set AZURE_STORAGE_SAMPLE_FILE to a local file path before running this example."
        )
    return file_path


async def main():
    async with AsyncStorageBlobHelper(account_name=require_account_name()) as helper:
        # Upload a file - library handles reading and content type detection
        await helper.upload_file(
            container_name="appfx-demo-container",
            blob_name="my-document.pdf",
            file_path=require_sample_file_path(),
            overwrite=True,
        )
        print("File uploaded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
