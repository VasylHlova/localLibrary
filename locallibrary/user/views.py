from django.views.generic import DetailView, UpdateView
from django.db.models import QuerySet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse 

from .models import CustomUser, UserProfile
from .forms import UpdateUserProfileForm

# Create your views here.

class UserDetail(LoginRequiredMixin, DetailView):
    model = CustomUser
    context_object_name = 'user'

    def get_queryset(self) -> QuerySet[CustomUser]:
        queryset = super().get_queryset()
        return queryset.select_related('profile').prefetch_related('borrowed_books__book')
    
    def get_context_data(self, **kwargs) -> dict:
        context =  super().get_context_data(**kwargs)
        context['is_owner'] = self.request.user.pk == self.object.pk

        return context
    

class UpdateUserProfile(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UpdateUserProfileForm
    template_name = 'user/edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user.profile
    
    def get_success_url(self):
        return reverse('user-detail', kwargs={'pk': self.request.user.pk})