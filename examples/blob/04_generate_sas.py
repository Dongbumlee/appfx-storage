"""
Generate SAS tokens - secure access made simple!
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
        # Generate a read-only SAS URL valid for 1 hour.
        # The returned URL is a bearer token; do not log, commit, or share it.
        _sas_url = await helper.generate_blob_sas_url(
            container_name="appfx-demo-container",
            blob_name="my-document.pdf",
            expiry_hours=1,
            permissions="r",  # read-only
        )

        print("Secure download link generated; not displaying sensitive SAS URL.")
        print("This link expires in 1 hour and allows download only.")


if __name__ == "__main__":
    asyncio.run(main())
