"""
Worker pattern - continuously process messages!
"""

import asyncio
import os

from appfx.storage import AsyncStorageQueueHelper


def require_account_name() -> str:
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "Set AZURE_STORAGE_ACCOUNT_NAME before running this live Azure example."
        )
    return account_name


async def worker(helper: AsyncStorageQueueHelper, queue_name: str, worker_id: int):
    """A worker that continuously processes messages"""
    print(f"Worker {worker_id} started")

    processed = 0
    while processed < 3:  # Process 3 messages then stop
        message = await helper.receive_message(queue_name, visibility_timeout=30)

        if message:
            print(f"Worker {worker_id} processing: {message['content']}")

            # Simulate processing work
            await asyncio.sleep(1)

            # Delete message after processing
            await helper.delete_message(
                queue_name, message["message_id"], message["pop_receipt"]
            )
            processed += 1
            print(f"Worker {worker_id} completed job {processed}")
        else:
            # No messages available, wait a bit
            await asyncio.sleep(2)

    print(f"Worker {worker_id} finished")


async def main():
    async with AsyncStorageQueueHelper(account_name=require_account_name()) as helper:
        queue_name = "worker-demo"
        await helper.create_queue(queue_name=queue_name)
        # Add some work items to the queue
        work_items = [f"Job {i}: Process customer order #{1000 + i}" for i in range(10)]

        await helper.send_messages_batch(queue_name, work_items)
        print(f"Added {len(work_items)} jobs to queue")

        # Start multiple workers concurrently
        workers = [
            worker(helper, queue_name, worker_id)
            for worker_id in range(1, 4)  # 3 workers
        ]

        # Run all workers concurrently
        await asyncio.gather(*workers)
        print("All workers completed!")


if __name__ == "__main__":
    asyncio.run(main())
