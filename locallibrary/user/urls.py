from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/profile', views.UserDetail.as_view(), name='user-detail'),
]