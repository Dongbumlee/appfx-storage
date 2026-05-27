import asyncio
import logging
import os

from appfx.storage import AsyncStorageBlobHelper


def require_account_name() -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_NAME before running this live Azure example."
        )
    return account_name


logging.basicConfig(level=logging.ERROR)


async def main():
    # await upload_blob()
    async with AsyncStorageBlobHelper(
        account_name=require_account_name()
    ) as blob_helper:
        if not await blob_helper.container_exists("appfx-demo-container"):
            await blob_helper.create_container("appfx-demo-container")

        await blob_helper.upload_blob(
            container_name="appfx-demo-container",
            blob_name="myblob.txt",
            data="Hello, World!",
            overwrite=True,
        )

        # Get SAS URL. The returned URL is a bearer token; do not log or commit it.
        _sas_url = await blob_helper.generate_blob_sas_url(
            container_name="appfx-demo-container",
            blob_name="myblob.txt",
            expiry_hours=24,
            permissions="r",
        )
        print("SAS URL generated; not displaying sensitive token.")


# application init
if __name__ == "__main__":
    asyncio.run(main())
