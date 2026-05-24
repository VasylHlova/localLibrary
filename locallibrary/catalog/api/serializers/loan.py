from rest_framework import serializers
from user.api.serializers import UserShortSerializer

from catalog.models import Loan


class LoanListSerializer(serializers.ModelSerializer):
    borrower: serializers.StringRelatedField = serializers.StringRelatedField()
    book_instance: serializers.StringRelatedField = serializers.StringRelatedField()

    is_overdue: serializers.BooleanField = serializers.BooleanField(read_only=True)
    overdue_days: serializers.IntegerField = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "borrower", "book_instance", "issued_at", "status", "is_overdue", "overdue_days"]


class LoanDetailSerializer(serializers.ModelSerializer):
    borrower: UserShortSerializer = UserShortSerializer(read_only=True)
    book_instance: serializers.HyperlinkedRelatedField = serializers.HyperlinkedRelatedField(
        view_name="api-instance-detail", read_only=True
    )

    is_overdue: serializers.BooleanField = serializers.BooleanField(read_only=True)
    overdue_days: serializers.IntegerField = serializers.IntegerField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id",
            "borrower",
            "book_instance",
            "issued_at",
            "returned_at",
            "status",
            "is_overdue",
            "overdue_days",
        ]
