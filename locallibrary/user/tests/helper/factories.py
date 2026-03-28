import io
import factory
from factory.django import DjangoModelFactory
from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile

class ImageFactory:
    @staticmethod
    def create(name="test.jpg", size=(100, 100), format="JPEG", content_type="image/jpeg"):
        file = io.BytesIO()
        Image.new("RGB", size, color="red").save(file, format=format)
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=content_type)

    @staticmethod
    def create_oversized(name="large.jpg", content_type="image/jpeg"):
        file = io.BytesIO()
        Image.new("RGB", (100, 100), color="red").save(file, format="JPEG")
        
        file.write(b"\0" * (21 * 1024 * 1024))
        file.seek(0)
        return SimpleUploadedFile(name, file.read(), content_type=content_type)

    @staticmethod
    def create_invalid_extension(name="test.pdf"):
        return SimpleUploadedFile(name, b"fake content", content_type="application/pdf")

class UserFactory(DjangoModelFactory):
    class Meta:
        model = "user.CustomUser"

    email = factory.Sequence(lambda n: f"user{n}@gmail.com")
    username = factory.Sequence(lambda n: f"username{n}")
    first_name = "John"
    last_name = "Doe"

class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = 'user.UserProfile'
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
