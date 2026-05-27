"""
Basic Upload and Download - Just 3 lines of core logic!
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
        # Upload text
        await helper.upload_blob(
            container_name="appfx-demo-container",
            blob_name="/mypath/yourpath/hello.txt",
            data="Hello, World!",
            overwrite=True,
        )

        # Download and print
        content = await helper.download_blob(
            "appfx-demo-container", "/mypath/yourpath/hello.txt"
        )
        print(content.decode())


if __name__ == "__main__":
    asyncio.run(main())
