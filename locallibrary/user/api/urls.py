from rest_framework.routers import DefaultRouter

from user.api.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="api-user")

urlpatterns = router.urls
