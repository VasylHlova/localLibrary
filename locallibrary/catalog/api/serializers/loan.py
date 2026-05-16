from rest_framework import serializers

from catalog.models import Loan
from user.api.serializers import UserShortSerializer


class LoanListSerializer(serializers.ModelSerializer):
    borrower = serializers.StringRelatedField()
    book_instance = serializers.StringRelatedField()

    class Meta:
        model = Loan
        fields = ['id', 'borrower', 'book_instance', 'issued_at', 'status', 'is_overdue', 'overdue_days']


class LoanDetailSerializer(serializers.ModelSerializer):
    borrower = UserShortSerializer(read_only=True)
    book_instance = serializers.HyperlinkedRelatedField(
        view_name='bookinstance-detail',
        read_only=True
    )

    class Meta:
        model = Loan
        fields = ['id', 'borrower', 'book_instance', 'issued_at', 'returned_at', 'status', 'is_overdue', 'overdue_days']