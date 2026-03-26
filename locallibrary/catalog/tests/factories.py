import io
import uuid
from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from catalog.models import Author, Genre, Language, Book, BookInstance, Loan
from utils.choices import InstanceStatus, LoanStatus


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
    first_name = "John"
    last_name = "Doe"


class AuthorFactory(DjangoModelFactory):
    class Meta:
        model = Author

    first_name = "Big"
    last_name = "Bob"
    date_of_birth = None
    date_of_death = None


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Genre {n}")


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = Language

    name = factory.Sequence(lambda n: f"Language {n}")


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"Book {n}")
    author = factory.SubFactory(AuthorFactory)
    summary = "Test summary"
    isbn = factory.Sequence(lambda n: str(n).zfill(13))
    language = factory.SubFactory(LanguageFactory)

    @factory.post_generation
    def genre(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for g in extracted:
                self.genre.add(g)
        else:
            self.genre.add(GenreFactory())


class BookInstanceFactory(DjangoModelFactory):
    class Meta:
        model = BookInstance

    id = factory.LazyFunction(uuid.uuid4)
    book = factory.SubFactory(BookFactory)
    imprint = "Test imprint"
    status = InstanceStatus.AVAILABLE
    due_back = None
    borrower = None


class AvailableBookInstanceFactory(BookInstanceFactory):
    status = InstanceStatus.AVAILABLE


class OnLoanBookInstanceFactory(BookInstanceFactory):
    status = InstanceStatus.ON_LOAN
    due_back = factory.LazyFunction(lambda: date.today() + timedelta(weeks=2))
    borrower = factory.SubFactory(UserFactory)


class OverdueBookInstanceFactory(BookInstanceFactory):
    status = InstanceStatus.ON_LOAN
    due_back = factory.LazyFunction(lambda: date.today() - timedelta(weeks=1))
    borrower = factory.SubFactory(UserFactory)


class LoanFactory(DjangoModelFactory):
    class Meta:
        model = Loan

    borrower = factory.SubFactory(UserFactory)
    book_instance = factory.SubFactory(OnLoanBookInstanceFactory)
    status = LoanStatus.ACTIVE