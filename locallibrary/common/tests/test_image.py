from io import BytesIO
from unittest.mock import MagicMock, patch

from common.image import GeneratePath, ImageProcessingMixin, process_image
from django.core.files.base import ContentFile
from PIL import Image


def test_process_image_none():
    assert process_image(None) is None


def test_process_image_valid():
    img = Image.new("RGB", (100, 100), color="red")
    b = BytesIO()
    img.save(b, "JPEG")
    b.seek(0)
    file = ContentFile(b.read(), name="test.jpg")

    processed = process_image(file, max_size=(50, 50))
    assert processed is not None
    processed_img = Image.open(processed)
    assert processed_img.format == "WEBP"
    assert processed_img.size == (50, 50)


def test_process_image_exception():
    file = ContentFile(b"not an image", name="test.jpg")
    processed = process_image(file)
    assert processed is None


def test_generate_path():
    path_generator = GeneratePath("images/")
    mock_instance = MagicMock()
    path = path_generator(mock_instance, "test.jpg")
    assert path.startswith("images/")
    assert path.endswith(".webp")


@patch("common.image.process_image")
def test_image_processing_mixin_save(mock_process_image):
    mock_process_image.return_value = ContentFile(b"processed", name="processed.webp")

    mock_image = MagicMock()
    mock_image.name = "original.jpg"


    class BaseModel:
        def save(self, *args, **kwargs):
            pass

    class TestModel(ImageProcessingMixin, BaseModel):
        IMAGE_FIELD = "image"

        def __init__(self, image=None):
            self.image = image
            super().__init__()

    old_image = MagicMock()
    old_image.name = "old.jpg"

    test_model = TestModel(image=old_image)  
    test_model.image = mock_image              
    test_model.save()

    mock_process_image.assert_called_once_with(mock_image, max_size=(800, 800))
    mock_image.save.assert_called_once_with("original.jpg", mock_process_image.return_value, save=False)
