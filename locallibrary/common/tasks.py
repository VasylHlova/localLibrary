from botocore.exceptions import (
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)
from celery import Task, shared_task
from django.core.files.storage import default_storage


@shared_task(
    name="common.cleanup_storage_file",
    bind=True,
    autoretry_for=(EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_jitter=True,
)
def cleanup_storage_file(self: Task, file_path: str) -> str:
    if file_path and default_storage.exists(file_path):
        default_storage.delete(file_path)
        return f"File {file_path} successfully deleted."
    return f"File {file_path} not found or path is empty."
