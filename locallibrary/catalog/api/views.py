from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import QuerySet


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
from locallibrary.catalog.api.filters import BookFilter
from catalog.api.serializers.genre import GenreSerializer
from catalog.api.serializers.language import LanguageSerializer
from catalog.api.serializers.author import AuthorBaseSerializer, AuthorWriteSerializer
from catalog.api.serializers.book import (
    BookListSerializer,
    BookDetailSerializer,
    BookWriteSerializer,
)
from catalog.api.serializers.book_instance import (
    BookInstanceListSerializer,
    BookInstanceDetailSerializer,
    BookInstanceCreateSerializer,
    BorrowOrReserveSerializer,
    BorrowReservedSerializer,
    RenewDueBackSerializer,
    ChangeStatusSerializer,
)
from catalog.api.serializers.loan import LoanDetailSerializer, LoanListSerializer


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class LanguageViewSet(ModelViewSet):
    queryset = Language.objects.all()
    serializer_class =LanguageSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = AuthorWriteSerializer

    serializer_classes = {
            'list': AuthorBaseSerializer,
            'retrieve': AuthorBaseSerializer,
    }
    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

class BookViewSet(ModelViewSet):
    queryset = Book.objects.all().order_by('title')
    
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    serializer_class = BookWriteSerializer 
    filterset_class = BookFilter
    serializer_classes = {
        'list': BookListSerializer,
        'retrieve': BookDetailSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'list':
            return queryset.select_related('author')
        if self.action == 'retrieve':
            return queryset.select_related('author', 'language').prefetch_related('genre')
        return queryset
    

class LoanReadViewSet(ReadOnlyModelViewSet):
    queryset = Loan.objects.select_related('borrower', 'book_instance')
    permission_classes = [StrictDjangoModelPermissions]
    filterset_fields = ['issued_at', 'is_overdue', 'overdue_days']
    serializer_class = LoanListSerializer
    serializer_classes = {
        'list': LoanListSerializer,
        'retrieve': LoanDetailSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    

class BookInstanceViewSet(ModelViewSet):
    queryset = BookInstance.objects.none()
    serializer_class = BookInstanceCreateSerializer
    filterset_fields = ['status']
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticatedOrReadOnly]

    serializer_classes = {
        'list': BookInstanceListSerializer,
        'retrieve': BookInstanceDetailSerializer,
        'create': BookInstanceCreateSerializer,
        'partial_update': ChangeStatusSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
    
    def get_queryset(self) -> QuerySet[BookInstance]:
        user = self.request.user
        
        if not user.is_authenticated:
            qs = BookInstance.objects.available_book_instances()
        elif user.has_perm('catalog.view_bookinstance'):
            qs = BookInstance.objects.all()
        else:
            qs = BookInstance.objects.available_book_instances() | BookInstance.objects.active_loans_by_user(user)
        
        return qs.select_related('book', 'borrower')
    

class BookActionViewSet(GenericViewSet):
    queryset = BookInstance.objects.none()
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def borrow_or_reserve(self, request, pk=None):
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
            return Response({"detail": "ok"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def borrow_reserved(self, request, pk=None):
        instance = self.get_object()
        serializer = BorrowReservedSerializer(data=request.data)

        if serializer.is_valid():
            try:
                borrow_reserved_book(
                    book_instance=instance,
                    user=request.user,
                    due_back= serializer.validated_data.get("due_back")
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "ok"}, status=status.HTTP_200_OK)
                        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[CanMarkReturned])
    def return_book(self, request, pk=None):
        instance = self.get_object()
        try:
            return_book(book_instance=instance)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "ok"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], permission_classes=[CanChangeDueBack])
    def extend_loan(self, request, pk=None):
        instance = self.get_object()
        serializer = RenewDueBackSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                renew_book(
                    book_instance=instance,
                    due_back= serializer.validated_data.get("due_back")
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": "ok"}, status=status.HTTP_200_OK)
                    
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)