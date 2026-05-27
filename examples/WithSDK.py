import os

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient


def require_account_name() -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_NAME before running this live Azure example."
        )
    return account_name


async def upload_blob():
    # Initialize Azure SDK client manually
    account_name = require_account_name()
    account_url = f"https://{account_name}.blob.core.windows.net"

    # Create credential (same as helper)
    credential = DefaultAzureCredential()

    # Create blob service client
    blob_service_client = BlobServiceClient(account_url, credential=credential)

    try:
        container_name = "appfx-demo-container"
        blob_name = "myblob.txt"
        data = "Hello, World!"

        # 1. Check if container exists (manual implementation)
        container_client = blob_service_client.get_container_client(container_name)
        container_exists = False

        try:
            await container_client.get_container_properties()
            container_exists = True
            print(f"Container '{container_name}' exists")
        except ResourceNotFoundError:
            container_exists = False
            print(f"Container '{container_name}' does not exist")
        except Exception as e:
            print(f"Error checking container existence: {e}")
            raise

        # 2. Create container if it doesn't exist (manual error handling)
        if not container_exists:
            try:
                await container_client.create_container()
                print(f"Container '{container_name}' created successfully")
            except ResourceExistsError:
                print(f"Container '{container_name}' already exists (race condition)")
            except Exception as e:
                print(f"Failed to create container '{container_name}': {e}")
                raise

        # 3. Upload blob (manual data conversion and content settings)
        blob_client = container_client.get_blob_client(blob_name)

        # Manual data conversion
        if isinstance(data, str):
            upload_data = data.encode("utf-8")
        else:
            upload_data = data

        # Manual content type detection
        import mimetypes

        content_type, _ = mimetypes.guess_type(blob_name)
        if content_type is None:
            content_type = "application/octet-stream"

        # Create content settings manually
        content_settings = ContentSettings(content_type=content_type)

        try:
            upload_result = await blob_client.upload_blob(
                upload_data,
                overwrite=True,
                content_settings=content_settings,
            )
            print(f"Blob '{blob_name}' uploaded successfully")
            print(f"Upload result: {upload_result}")
        except Exception as e:
            print(f"Failed to upload blob '{blob_name}': {e}")
            raise
    finally:
        # Manual cleanup - very important!
        try:
            await blob_service_client.close()
            await credential.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
