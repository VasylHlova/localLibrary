import pytest
from unittest.mock import patch, MagicMock
from django.core.files.base import ContentFile
from common.image import process_image, GeneratePath, ImageProcessingMixin
from PIL import Image
from io import BytesIO

def test_process_image_none():
    assert process_image(None) is None

def test_process_image_valid():
    img = Image.new('RGB', (100, 100), color='red')
    b = BytesIO()
    img.save(b, 'JPEG')
    b.seek(0)
    file = ContentFile(b.read(), name="test.jpg")
    
    processed = process_image(file, max_size=(50, 50))
    assert processed is not None
    processed_img = Image.open(processed)
    assert processed_img.format == 'WEBP'
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

class DummyModel(ImageProcessingMixin):
    IMAGE_FIELD = "image"
    def __init__(self, image=None):
        self.image = image
        super().__init__()
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

@patch('common.image.process_image')
def test_image_processing_mixin_save(mock_process_image):
    mock_process_image.return_value = ContentFile(b"processed", name="processed.webp")
    
    mock_image = MagicMock()
    mock_image.name = "original.jpg"
    
    model = DummyModel(image=mock_image)
    
    class BaseModel:
        def save(self, *args, **kwargs):
            pass

    class TestModel(ImageProcessingMixin, BaseModel):
        IMAGE_FIELD = "image"
        def __init__(self, image=None):
            self.image = image
            super().__init__()

    test_model = TestModel(image=mock_image)
    test_model.save()
    
    mock_process_image.assert_called_once_with(mock_image, max_size=(800, 800))
    mock_image.save.assert_called_once_with("original.jpg", mock_process_image.return_value, save=False)
