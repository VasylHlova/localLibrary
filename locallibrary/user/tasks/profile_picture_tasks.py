from celery import shared_task

from django.core.files.storage import default_storage
from botocore.exceptions import (
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
)

@shared_task(
    name='common.cleanup_needless_profile_picture', 
    bind=True,
    autoretry_for=(
            EndpointConnectionError, 
            ConnectTimeoutError, 
            ReadTimeoutError
        ),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True, 
    retry_jitter=True
)
def cleanup_needless_profile_picture(self, file_path: str):
    if file_path and default_storage.exists(file_path):
        default_storage.delete(file_path)
        return f"File {file_path} successfully deleted from storage."
    
    return f"File {file_path} not found in storage or path is empty."