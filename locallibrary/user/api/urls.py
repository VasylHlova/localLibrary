from rest_framework.routers import DefaultRouter

from user.api.views import UserViewSet, UserRegistrationViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="api-user")
router.register(r"auth", UserRegistrationViewSet, basename="auth")

urlpatterns = router.urls
