"""
Batch operations - upload multiple files at once!
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
        # Prepare multiple uploads
        files_to_upload = [
            ("file1.txt", "Content of file 1"),
            ("file2.txt", "Content of file 2"),
            ("file3.txt", "Content of file 3"),
        ]

        # Upload all files concurrently - much faster!
        tasks = []
        for filename, content in files_to_upload:
            task = helper.upload_blob(
                container_name="appfx-demo-container",
                blob_name=filename,
                data=content,
                overwrite=True,
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        print(f"Uploaded {len(files_to_upload)} files concurrently!")


if __name__ == "__main__":
    asyncio.run(main())
