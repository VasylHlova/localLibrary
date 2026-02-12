from django.views.generic import DetailView
from django.db.models import QuerySet

from .models import CustomUser, UserProfile

# Create your views here.

class UserDetail(DetailView):
    model = CustomUser
    context_object_name = 'user'

    def get_queryset(self) -> QuerySet[CustomUser]:
        queryset = super().get_queryset()
        return queryset.select_related('profile').prefetch_related('borrowed_books__book')
    
    def get_context_data(self, **kwargs) -> dict:
        context =  super().get_context_data(**kwargs)
        context['is_owner'] = self.request.user.pk == self.object.pk

        return context