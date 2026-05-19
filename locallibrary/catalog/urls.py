from django.urls import path

from catalog import views

urlpatterns = [
    path("", views.index, name="index"),
    path("books/", views.BookListView.as_view(), name="books"),
    path("book/<int:pk>", views.BookDetailView.as_view(), name="book-detail"),
    path("book/create/", views.BookCreate.as_view(), name="book-create"),
    path("book/<int:pk>/update/", views.BookUpdate.as_view(), name="book-update"),
    path("book/<int:pk>/delete/", views.BookDelete.as_view(), name="book-delete"),
    path("mybooks/", views.UserBorrowedBooksListView.as_view(), name="my-borrowed"),
    path("mybooks/<uuid:pk>/borrow/", views.BorrowReservedBookView.as_view(), name="bookinstance-borrow-reserved"),
    path("borrowedbooks/", views.AllBorrowedBooksListView.as_view(), name="all-borrowed"),
    path("book/<uuid:pk>/renew/", views.RenewBookLibrarianView.as_view(), name="bookinstance-renew"),
    path("book/<uuid:pk>/borrow/", views.BorrowOrReserveBookView.as_view(), name="bookinstance-borrow"),
    path("book/<uuid:pk>/return/", views.return_book_view, name="bookinstance-return"),
    path(
        "book/<uuid:pk>/status/change/",
        views.ChangeBookStatusView.as_view(),
        name="bookinstance-change-status",
    ),
    path("authors/", views.AuthorListView.as_view(), name="authors"),
    path("author/<int:pk>", views.AuthorDetailView.as_view(), name="author-detail"),
    path("author/create/", views.AuthorCreate.as_view(), name="author-create"),
    path("author/<int:pk>/update/", views.AuthorUpdate.as_view(), name="author-update"),
    path("author/<int:pk>/delete/", views.AuthorDelete.as_view(), name="author-delete"),
]
