from common.cache import DRFUserVersionedCacheListMixin, DRFVersionedCacheListMixin
from common.mixins import MultiPermissionMixin, MultiSerializerMixin
from common.permissions import StrictDjangoModelPermissions
from django.db.models import ProtectedError, Q, QuerySet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from catalog.api.filters import AuthorFilter, BookFilter, BookInstanceFilter, LoanFilter
from catalog.api.permissions import (
    CanChangeDueBack,
    CanChangeStatus,
    CanMarkReturned,
)
from catalog.api.serializers import (
    AuthorBaseSerializer,
    AuthorWriteSerializer,
    BookDetailSerializer,
    BookInstanceCreateSerializer,
    BookInstanceDetailSerializer,
    BookInstanceListSerializer,
    BookListSerializer,
    BookWriteSerializer,
    BorrowOrReserveSerializer,
    BorrowReservedSerializer,
    ChangeStatusSerializer,
    GenreSerializer,
    LanguageSerializer,
    LoanDetailSerializer,
    LoanListSerializer,
    RenewDueBackSerializer,
)
from catalog.choices import InstanceStatus
from catalog.models import Author, Book, BookInstance, Genre, Language, Loan
from catalog.services import borrow_or_reserve_book, borrow_reserved_book, renew_book, return_book


def get_book_instance_queryset(user: "Request.user") -> "QuerySet[BookInstance]":
    if not user.is_authenticated:
        return BookInstance.objects.available_book_instances()
    if user.has_perm("catalog.view_bookinstance"):
        return BookInstance.objects.all()
    return BookInstance.objects.filter(
        Q(status=InstanceStatus.AVAILABLE)
        | Q(
            status__in=[InstanceStatus.ON_LOAN, InstanceStatus.RESERVED],
            borrower=user,
        )
    )


class GenreViewSet(DRFVersionedCacheListMixin, ModelViewSet):
    queryset = Genre.objects.all().order_by("id")
    serializer_class = GenreSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filterset_fields = ["name"]


class LanguageViewSet(DRFVersionedCacheListMixin, ModelViewSet):
    queryset = Language.objects.all().order_by("id")
    serializer_class = LanguageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class AuthorViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ModelViewSet):
    queryset = Author.objects.all().order_by("id")
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AuthorWriteSerializer
    filterset_class = AuthorFilter

    serializer_classes = {
        "list": AuthorBaseSerializer,
        "retrieve": AuthorBaseSerializer,
    }

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete this author because they have related books."},
                status=status.HTTP_409_CONFLICT,
            )


class BookViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ModelViewSet):
    queryset = Book.objects.all().order_by("title", "id")

    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = BookWriteSerializer
    filterset_class = BookFilter
    serializer_classes = {
        "list": BookListSerializer,
        "retrieve": BookDetailSerializer,
    }

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "list":
            return queryset.select_related("author")
        if self.action == "retrieve":
            return queryset.select_related("author", "language").prefetch_related("genre")
        return queryset

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete this book because it has related instances."},
                status=status.HTTP_409_CONFLICT,
            )


class LoanReadViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ReadOnlyModelViewSet):
    queryset = Loan.objects.select_related("borrower", "book_instance").order_by("id")
    permission_classes = [StrictDjangoModelPermissions]
    filterset_class = LoanFilter
    serializer_class = LoanListSerializer
    serializer_classes = {
        "list": LoanListSerializer,
        "retrieve": LoanDetailSerializer,
    }


class BookInstanceViewSet(
    DRFUserVersionedCacheListMixin, MultiPermissionMixin, MultiSerializerMixin, ModelViewSet
):
    queryset = BookInstance.objects.none()
    filterset_class = BookInstanceFilter
    permission_classes = [StrictDjangoModelPermissions]
    serializer_class = BookInstanceListSerializer

    serializer_classes = {
        "list": BookInstanceListSerializer,
        "retrieve": BookInstanceDetailSerializer,
        "create": BookInstanceCreateSerializer,
        "partial_update": ChangeStatusSerializer,
    }

    permission_classes_by_action = {
        "partial_update": [CanChangeStatus],
        "my": [IsAuthenticated],
    }

    def get_queryset(self) -> QuerySet[BookInstance]:
        return (
            get_book_instance_queryset(self.request.user)
            .select_related("book", "borrower", "book__author")
            .order_by("due_back", "id")
        )

    @action(detail=False, methods=["get"])
    def my(self, request: Request) -> Response:
        qs = (
            BookInstance.objects.active_loans_by_user(request.user)
            .select_related("book", "borrower", "book__author")
            .order_by("due_back")
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = BookInstanceListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = BookInstanceListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class BookActionViewSet(GenericViewSet):
    queryset = BookInstance.objects.none()
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[BookInstance]:
        return get_book_instance_queryset(self.request.user)

    @action(detail=True, methods=["post"])
    def borrow_or_reserve(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = BorrowOrReserveSerializer(data=request.data)

        if serializer.is_valid():
            try:
                borrow_or_reserve_book(
                    book_instance=instance,
                    user=request.user,
                    due_back=serializer.validated_data.get("due_back"),
                    status=serializer.validated_data.get("status"),
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={"request": request}).data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def borrow_reserved(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = BorrowReservedSerializer(data=request.data)

        if serializer.is_valid():
            try:
                borrow_reserved_book(
                    book_instance=instance,
                    user=request.user,
                    due_back=serializer.validated_data.get("due_back"),
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={"request": request}).data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[CanMarkReturned])
    def return_book(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        try:
            return_book(book_instance=instance)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            BookInstanceDetailSerializer(instance, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["patch"], permission_classes=[CanChangeDueBack])
    def extend_loan(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = RenewDueBackSerializer(instance, data=request.data)

        if serializer.is_valid():
            try:
                renew_book(book_instance=instance, due_back=serializer.validated_data.get("due_back"))
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={"request": request}).data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
