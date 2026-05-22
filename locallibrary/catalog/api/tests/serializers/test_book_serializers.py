import pytest
from rest_framework.test import APIRequestFactory

from catalog.api.serializers.book import (
    BookBaseSerializer,
    BookDetailSerializer,
    BookListSerializer,
    BookShortSerializer,
    BookWriteSerializer,
)
from catalog.tests.helper.factories import AuthorFactory, BookFactory, GenreFactory, LanguageFactory

pytestmark = pytest.mark.django_db


def test_book_base_serialization():
    book = BookFactory()
    serializer = BookBaseSerializer(instance=book)
    assert serializer.data["title"] == book.title
    assert "author" in serializer.data
    assert "image" in serializer.data


def test_book_short_serialization():
    author = AuthorFactory()
    book = BookFactory(author=author)
    factory = APIRequestFactory()
    request = factory.get("/api/catalog/books/")
    serializer = BookShortSerializer(instance=book, context={"request": request})
    assert serializer.data["title"] == book.title
    assert serializer.data["author"] == f"{author.first_name} {author.last_name}"
    assert serializer.data["detail_url"].endswith(f"/api/catalog/books/{book.pk}/")


def test_book_list_serialization():
    author = AuthorFactory()
    book = BookFactory(author=author)
    factory = APIRequestFactory()
    request = factory.get("/api/catalog/books/")
    serializer = BookListSerializer(instance=book, context={"request": request})
    assert serializer.data["title"] == book.title
    assert serializer.data["author"]["first_name"] == author.first_name
    assert serializer.data["author"]["detail_url"].endswith(f"/api/catalog/authors/{author.pk}/")


def test_book_detail_serialization():
    author = AuthorFactory()
    language = LanguageFactory()
    genre = GenreFactory()
    book = BookFactory(author=author, language=language)
    book.genre.add(genre)

    factory = APIRequestFactory()
    request = factory.get("/api/catalog/books/")
    serializer = BookDetailSerializer(instance=book, context={"request": request})
    assert serializer.data["title"] == book.title
    assert serializer.data["author"]["last_name"] == author.last_name
    assert serializer.data["language"]["name"] == language.name
    assert serializer.data["genre"][0]["name"] == genre.name


def test_book_write_validation_success():
    author = AuthorFactory()
    language = LanguageFactory()
    genre = GenreFactory()
    data = {
        "title": "A Random Book Title",
        "summary": "Some summary",
        "isbn": "9781234567897",
        "author": author.pk,
        "language": language.pk,
        "genre": [genre.pk],
    }
    serializer = BookWriteSerializer(data=data)
    assert serializer.is_valid()


def test_book_write_validation_missing_required():
    data = {
        "summary": "No title",
    }
    serializer = BookWriteSerializer(data=data)
    assert not serializer.is_valid()
    assert "title" in serializer.errors
