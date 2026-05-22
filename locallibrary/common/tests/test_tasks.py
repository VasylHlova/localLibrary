from unittest.mock import patch

from common.tasks import cleanup_storage_file


@patch("common.tasks.default_storage")
def test_cleanup_storage_file_exists(mock_storage):
    mock_storage.exists.return_value = True
    result = cleanup_storage_file("path/to/file.jpg")
    mock_storage.delete.assert_called_once_with("path/to/file.jpg")
    assert result == "File path/to/file.jpg successfully deleted."


@patch("common.tasks.default_storage")
def test_cleanup_storage_file_not_found(mock_storage):
    mock_storage.exists.return_value = False
    result = cleanup_storage_file("path/to/missing.jpg")
    mock_storage.delete.assert_not_called()
    assert result == "File path/to/missing.jpg not found or path is empty."
