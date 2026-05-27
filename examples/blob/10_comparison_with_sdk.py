"""
Compare: Raw Azure SDK vs appfx-storage library.

See how much simpler your code becomes!
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


# ❌ Raw Azure SDK - Complex and verbose
"""
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
import asyncio
import aiohttp
import os

async def upload_with_raw_sdk():
    # Setup credentials and client
    credential = DefaultAzureCredential()
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    account_url = f"https://{account_name}.blob.core.windows.net"
    
    async with BlobServiceClient(
        account_url=account_url, 
        credential=credential
    ) as client:
        # Get container client
        container_client = client.get_container_client("appfx-demo-container")
        
        # Create container if not exists
        try:
            await container_client.create_container()
        except Exception:
            pass  # Already exists
        
        # Get blob client
        blob_client = client.get_blob_client(
            container="appfx-demo-container", 
            blob="test.txt"
        )
        
        # Upload data
        await blob_client.upload_blob(
            "Hello World!", 
            overwrite=True
        )
"""


async def upload_with_helper():
    async with AsyncStorageBlobHelper(account_name=require_account_name()) as helper:
        await helper.upload_blob(
            "appfx-demo-container", "test.txt", "Hello World!", overwrite=True
        )


# The difference is obvious:
# - Raw SDK: ~25 lines, complex setup, error handling, multiple clients
# - Helper: 3 lines, automatic setup, built-in error handling, one client

if __name__ == "__main__":
    print("Raw SDK: 25+ lines of complex code")
    print("Helper:  3 lines of simple code")
    print("That's 88% less code for the same result!")

    asyncio.run(upload_with_helper())
