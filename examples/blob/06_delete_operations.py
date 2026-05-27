"""
Delete blobs and containers - clean and simple!
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
        container_name = "appfx-delete-demo"
        blob_name = "delete-me.txt"

        # Create an isolated demo resource before deleting it.
        await helper.create_container(container_name)
        await helper.upload_blob(
            container_name,
            blob_name,
            "Temporary content created by the delete example.",
            overwrite=True,
        )

        await helper.delete_blob(container_name, blob_name)
        print("Demo blob deleted!")

        # The container is empty now, so default delete behavior is safe.
        await helper.delete_container(container_name)
        print("Demo container deleted!")


if __name__ == "__main__":
    asyncio.run(main())
