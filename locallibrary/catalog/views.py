from typing import Any
from uuid import uuid4

from utils.choices import InstanceStatus
from utils.cache import VersionedCacheListMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, QuerySet
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import BorrowOrReserveBookForm, ChangeBookStatusForm, RenewBookForm
from .models import Author, Book, BookInstance


def index(request: HttpRequest) -> HttpResponse:

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.filter(status__exact="a").count()

    num_authors = Author.objects.count()
    num_visits = request.session.get("num_visits", 0)

    num_visits += 1
    request.session["num_visits"] = num_visits

    context = {
        "num_books": num_books,
        "num_instances": num_instances,
        "num_instances_available": num_instances_available,
        "num_authors": num_authors,
        "num_visits": num_visits,
    }

    return render(request, "index.html", context=context)


class AuthorListView(VersionedCacheListMixin, ListView):
    model = Author
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Author]:
        return Author.objects.prefetch_related("books")


class AuthorDetailView(DetailView):
    model = Author


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death", "image"]
    initial = {"date_of_birth": "31.12.2020"}
    permission_required = "catalog.add_author"


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = "__all__"
    permission_required = "catalog.change_author"


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy("authors")
    permission_required = "catalog.delete_author"

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            return HttpResponseRedirect(reverse("author-delete", kwargs={"pk": self.object.pk}))


class BookListView(VersionedCacheListMixin, ListView):
    model = Book
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Book]:
        return Book.objects.select_related("author").prefetch_related("genre").order_by('title')


class BookDetailView(DetailView):
    model = Book


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "image", 'language']
    permission_required = "catalog.add_book"


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = "__all__"
    permission_required = "catalog.change_book"


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy("books")
    permission_required = "catalog.delete_book"

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            return HttpResponseRedirect(reverse("book-delete", kwargs={"pk": self.object.pk}))


class LoanBookInstanceByUserListView(LoginRequiredMixin, VersionedCacheListMixin, ListView):
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 10

    def get_cache_prefix(self):
        base_prefix = super().get_cache_prefix()

        return f"{base_prefix}_user_{self.request.user.id}"

    def get_queryset(self) -> QuerySet[BookInstance]:
        return (
            BookInstance.objects.select_related("book", "borrower")
            .filter(borrower=self.request.user)
            .filter(Q(status=InstanceStatus.ON_LOAN) | Q(status=InstanceStatus.RESERVED))
            .order_by("due_back")
        )


class LoanBookInstanceListView(LoginRequiredMixin, PermissionRequiredMixin, VersionedCacheListMixin, ListView):
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed.html"
    permission_required = "catalog.can_mark_returned", "catalog.view_bookinstance"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[BookInstance]:
        return (
            BookInstance.objects.select_related("book", "borrower")
            .filter(Q(status=InstanceStatus.ON_LOAN) | Q(status=InstanceStatus.RESERVED))
            .order_by("due_back")
        )


class RenewBookInstanceLibrarian(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = BookInstance
    form_class = RenewBookForm
    template_name = "catalog/book_renew_librarian.html"
    success_url = reverse_lazy("all-borrowed")
    permission_required = "catalog.change_bookinstance"


class BorrowOrReserveBookInstance(LoginRequiredMixin, UpdateView):
    model = BookInstance
    form_class = BorrowOrReserveBookForm

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None) -> BookInstance:
        queryset = self.get_queryset()
        if self.request.method == "POST":
            queryset = queryset.select_for_update()
        return super().get_object(queryset)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("my-borrowed")


class ChangeBookInstanceStatus(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    form_class = ChangeBookStatusForm
    permission_required = [
        "catalog.can_change_status",
    ]
    template_name = "catalog/book_change_status.html"
    success_url = reverse_lazy("all-borrowed")


@login_required
@permission_required(perm="catalog.can_mark_returned", raise_exception=True)
@require_POST
def return_bookinstance(request, pk: uuid4) -> None:
    instance = get_object_or_404(BookInstance, pk=pk)

    try:
        instance.return_book()
        messages.success(request, f"Book '{instance.book.title}' ({instance.id}) successfuly returned.")
    except Exception as e:
        messages.error(request, f"Error during returning: {e}")

    return redirect("all-borrowed")
