from rest_framework import serializers

from catalog.models import Book
from catalog.api.serializers.author import AuthorShortSerializer
from catalog.api.serializers.genre import GenreSerializer
from catalog.api.serializers.language import LanguageSerializer


class BaseBookSerialyzer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id','title', 'author', 'image']


class BookListSerializer(BaseBookSerialyzer):
    author = AuthorShortSerializer(read_only=True)


class BookDetailSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    author = AuthorShortSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'summary', 'isbn', 'author', 'genre', 'language', 'image']


class BookWriteSerializer(BaseBookSerialyzer):
    ...