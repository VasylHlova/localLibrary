from django.urls import path

from user import views

urlpatterns = [
    path("<int:pk>/profile", views.UserDetail.as_view(), name="user-detail"),
    path("<int:pk>/profile/edit", views.UpdateUserProfile.as_view(), name="profile-edit"),
]
