import django_filters
from django.db.models import Value, Q, F
from django.db.models.functions import Concat, Now
from catalog.models import Book, Loan


class BookFilter(django_filters.FilterSet):
    author_name = django_filters.CharFilter(method='filter_by_author_full_name')

    class Meta:
        model = Book
        fields = ['title']

    def filter_by_author_full_name(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.annotate(
            full_name=Concat('author__first_name', Value(' '), 'author__last_name')
        ).filter(full_name__icontains=value)
    

class LoanFilter(django_filters.FilterSet):
    is_overdue = django_filters.BooleanFilter(method='filter_is_overdue')

    class Meta:
        model = Loan
        fields = ['issued_at']

    def filter_is_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(returned_at__isnull=True, book_instance__due_back__lt=Now()) |
                Q(returned_at__isnull=False, returned_at__gt=F('book_instance__due_back'))
            )

        else:
            return queryset.exclude(
                Q(returned_at__isnull=True, book_instance__due_back__lt=Now()) |
                Q(returned_at__isnull=False, returned_at__gt=F('book_instance__due_back'))
            ) 
