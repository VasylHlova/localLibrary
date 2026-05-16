from rest_framework import serializers

from catalog.models import Genre


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields= ['id', 'name']

