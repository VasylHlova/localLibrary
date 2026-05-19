from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import QuerySet

from utils.cache import DRFVersionedCacheListMixin, DRFUserVersionedCacheListMixin
from catalog.models import (
    Genre, Language,
    Author, Book,
    BookInstance, Loan
)
from catalog.services import (
    borrow_or_reserve_book,
    borrow_reserved_book,
    renew_book,
    return_book
)
from catalog.api.permissions import (
    StrictDjangoModelPermissions,
    CanChangeDueBack,
    CanMarkReturned,
)
from catalog.api.filters import BookFilter, LoanFilter
from catalog.api.serializers import (
    GenreSerializer,
    LanguageSerializer,
    AuthorBaseSerializer, 
    AuthorWriteSerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookWriteSerializer,
    BookInstanceListSerializer,
    BookInstanceDetailSerializer,
    BookInstanceCreateSerializer,
    BorrowOrReserveSerializer,
    BorrowReservedSerializer,
    RenewDueBackSerializer,
    ChangeStatusSerializer,
    LoanDetailSerializer, 
    LoanListSerializer
)


class MultiSerializerMixin:
    serializer_classes = {}
    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, super().get_serializer_class())


class GenreViewSet(DRFVersionedCacheListMixin, ModelViewSet):
    queryset = Genre.objects.all().order_by('id')
    serializer_class = GenreSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class LanguageViewSet(DRFVersionedCacheListMixin, ModelViewSet):
    queryset = Language.objects.all().order_by('id')
    serializer_class = LanguageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class AuthorViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ModelViewSet):
    queryset = Author.objects.all().order_by('id')
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AuthorWriteSerializer

    serializer_classes = {
        'list': AuthorBaseSerializer,
        'retrieve': AuthorBaseSerializer,
    }


class BookViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ModelViewSet):
    queryset = Book.objects.all().order_by('title', 'id')
    
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = BookWriteSerializer 
    filterset_class = BookFilter
    serializer_classes = {
        'list': BookListSerializer,
        'retrieve': BookDetailSerializer,
    }

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'list':
            return queryset.select_related('author')
        if self.action == 'retrieve':
            return queryset.select_related('author', 'language').prefetch_related('genre')
        return queryset
    

class LoanReadViewSet(DRFVersionedCacheListMixin, MultiSerializerMixin, ReadOnlyModelViewSet):
    queryset = Loan.objects.select_related('borrower', 'book_instance').order_by('id')
    permission_classes = [StrictDjangoModelPermissions]
    filterset_class = LoanFilter
    serializer_class = LoanListSerializer
    serializer_classes = {
        'list': LoanListSerializer,
        'retrieve': LoanDetailSerializer,
    }


class BookInstanceViewSet(DRFUserVersionedCacheListMixin, MultiSerializerMixin, ModelViewSet):
    queryset = BookInstance.objects.none()
    filterset_fields = ['status', 'borrower', 'book__title']
    permission_classes = [StrictDjangoModelPermissions]

    serializer_classes = {
        'list': BookInstanceListSerializer,
        'retrieve': BookInstanceDetailSerializer,
        'create': BookInstanceCreateSerializer,
        'partial_update': ChangeStatusSerializer,
    }

    def get_queryset(self) -> QuerySet[BookInstance]:
        user = self.request.user
        
        if not user.is_authenticated:
            qs = BookInstance.objects.available_book_instances().order_by('id')
        elif user.has_perm('catalog.view_bookinstance'):
            qs = BookInstance.objects.all().order_by('id')
        else:
            qs = BookInstance.objects.available_book_instances() | BookInstance.objects.active_loans_by_user(user).order_by('-due_back', 'id')
        
        return qs.select_related('book', 'borrower', 'book__author').order_by('id')
    

class BookActionViewSet(GenericViewSet):
    queryset = BookInstance.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def borrow_or_reserve(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = BorrowOrReserveSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                borrow_or_reserve_book(
                    book_instance=instance,
                    user=request.user,
                    due_back=serializer.validated_data.get("due_back"),
                    status=serializer.validated_data.get("status")
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={'request': request}).data, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def borrow_reserved(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = BorrowReservedSerializer(data=request.data)

        if serializer.is_valid():
            try:
                borrow_reserved_book(
                    book_instance=instance,
                    user=request.user,
                    due_back=serializer.validated_data.get("due_back")
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={'request': request}).data, 
                status=status.HTTP_200_OK
            )
                        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[CanMarkReturned])
    def return_book(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        try:
            return_book(book_instance=instance)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            BookInstanceDetailSerializer(instance, context={'request': request}).data, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['patch'], permission_classes=[CanChangeDueBack])
    def extend_loan(self, request: Request, pk: str | None = None) -> Response:
        instance = self.get_object()
        serializer = RenewDueBackSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                renew_book(
                    book_instance=instance,
                    due_back=serializer.validated_data.get("due_back")
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                BookInstanceDetailSerializer(instance, context={'request': request}).data, 
                status=status.HTTP_200_OK
            )
                    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)