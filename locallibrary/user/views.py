from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import DetailView, UpdateView

from user.forms import UpdateUserProfileForm
from user.models import CustomUser, UserProfile


class UserDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CustomUser
    context_object_name = "user"

    def get_object(self, queryset=None):
        # Cache to avoid a second DB hit from UserPassesTestMixin calling
        # get_object() during test_func() and then Django calling it again
        # in get().
        if not hasattr(self, '_object'):
            self._object = super().get_object(queryset)
        return self._object

    def test_func(self) -> bool:
        return (
            self.request.user.pk == self.get_object().pk
            or self.request.user.has_perm('auth.view_user')
        )

    def get_queryset(self) -> QuerySet[CustomUser]:
        return (
            super().get_queryset()
            .select_related("profile")
            .prefetch_related("borrowed_books__book")
        )

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["is_owner"] = self.request.user.pk == self.object.pk
        return context


class UpdateUserProfile(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UpdateUserProfileForm
    template_name = "user/edit_profile.html"

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_success_url(self):
        return reverse("user-detail", kwargs={"pk": self.request.user.pk})
