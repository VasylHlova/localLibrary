from rest_framework.routers import DefaultRouter

from catalog.api.views import (
    AuthorViewSet,
    BookActionViewSet,
    BookInstanceViewSet,
    BookViewSet,
    GenreViewSet,
    LanguageViewSet,
    LoanReadViewSet,
)

router = DefaultRouter()
router.register(r"languages", LanguageViewSet, basename="api-language")
router.register(r"genres", GenreViewSet, basename="api-genre")
router.register(r"authors", AuthorViewSet, basename="api-author")
router.register(r"books", BookViewSet, basename="api-book")
router.register(r"instances", BookInstanceViewSet, basename="api-instance")
router.register(r"actions", BookActionViewSet, basename="api-instance-action")
router.register(r"loans", LoanReadViewSet, basename="api-loan")

urlpatterns = router.urls
