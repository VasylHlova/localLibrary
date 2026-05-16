from rest_framework import serializers

from catalog.models import BookInstance
from utils.choices import InstanceStatus


class BookInstanceListSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = BookInstance
        field = ['id', 'book__title', 'status', 'imprint', 'due_back', 'borrower', 'is_overdue']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
            data.pop("is_overdue")
            data.pop("borrower")
            data.pop("due_back")
        return data
    

class BookInstanceDetailSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = BookInstance
        field = ['id', 'book__title', 'status', 'imprint', 'due_back', 'borrower', 'is_overdue']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
            data.pop("is_overdue")
            data.pop("borrower")
            data.pop("due_back")
        return data