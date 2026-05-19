from rest_framework import serializers

from catalog.models import Author


class AuthorBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'date_of_birth', 'date_of_death', 'image']


class AuthorShortSerializer(serializers.ModelSerializer):
    detail_url = serializers.HyperlinkedIdentityField(view_name='api-author-detail')

    class Meta:
        model = Author
        fields = ['id', 'first_name', 'last_name', 'detail_url']


class AuthorWriteSerializer(AuthorBaseSerializer):
    def validate(self, attrs) -> dict:
        born = attrs.get("date_of_birth")
        died = attrs.get("date_of_death")

        if died and born:
            if died < born:
                raise serializers.ValidationError("Author could not die earlier than was born!")
            
        return attrs