from rest_framework.pagination import PageNumberPagination
from django.db.models import QuerySet

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100 
    

    max_count = 10000 

    def get_count(self, queryset: QuerySet) -> int:
        limited_qs = queryset.values('pk')[:self.max_count]
        count = limited_qs.count()
        
        if count == self.max_count:
            return self.max_count
            
        return count