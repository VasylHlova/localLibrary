import django_filters
from django.db.models import Value
from django.db.models.functions import Concat
from catalog.models import Book

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
    
