from uuid import uuid4

from common.cache import VersionedCacheListMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Model, ProtectedError, QuerySet
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from catalog.forms import (
    BorrowOrReserveBookForm,
    BorrowReservedBookForm,
    ChangeBookStatusForm,
    RenewBookForm,
)
from catalog.models import (
    Author,
    Book,
    BookInstance,
)
from catalog.services import (
    borrow_or_reserve_book,
    borrow_reserved_book,
    renew_book,
    return_book,
)


def index(request: HttpRequest) -> HttpResponse:

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.available_book_instances().count()

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

    def get_queryset(self):
        return super().get_queryset().prefetch_related("books__instances")


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death", "image"]
    initial = {"date_of_birth": "31.12.2020"}
    permission_required = "catalog.add_author"


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death", "image"]
    permission_required = "catalog.change_author"


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy("authors")
    permission_required = "catalog.delete_author"

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this author because they have related books.")
            return HttpResponseRedirect(reverse("author-delete", kwargs={"pk": self.object.pk}))


class BookListView(VersionedCacheListMixin, ListView):
    model = Book
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Book]:
        return Book.objects.select_related("author").prefetch_related("genre").order_by("title")


class BookDetailView(DetailView):
    model = Book

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("author", "language")
            .prefetch_related("instances", "genre")
        )


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "image", "language"]
    permission_required = "catalog.add_book"


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ["title", "author", "summary", "isbn", "genre", "image", "language"]
    permission_required = "catalog.change_book"


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy("books")
    permission_required = "catalog.delete_book"

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except ProtectedError:
            messages.error(self.request, "Cannot delete this book because it has related instances.")
            return HttpResponseRedirect(reverse("book-delete", kwargs={"pk": self.object.pk}))


class UserBorrowedBooksListView(LoginRequiredMixin, VersionedCacheListMixin, ListView):
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed_user.html"
    paginate_by = 10

    def get_cache_prefix(self, model: Model) -> str:
        base_prefix = super().get_cache_prefix(model)

        return f"{base_prefix}_user_{self.request.user.id}"

    def get_queryset(self) -> QuerySet[BookInstance]:
        return (
            BookInstance.objects.active_loans_by_user(user=self.request.user)
            .select_related("book__author", "borrower")
            .order_by("due_back")
        )


class AllBorrowedBooksListView(
    LoginRequiredMixin, PermissionRequiredMixin, VersionedCacheListMixin, ListView
):
    model = BookInstance
    template_name = "catalog/bookinstance_list_borrowed.html"
    permission_required = "catalog.can_mark_returned", "catalog.view_bookinstance"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[BookInstance]:
        return (
            BookInstance.objects.active_loans()
            .select_related("book__author", "borrower")
            .order_by("due_back")
        )


class RenewBookLibrarianView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = BookInstance
    form_class = RenewBookForm
    template_name = "catalog/book_renew_librarian.html"
    success_url = reverse_lazy("all-borrowed")
    permission_required = "catalog.change_bookinstance"

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            renew_book(book_instance=self.object, due_back=form.cleaned_data.get("due_back"))
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class BorrowReservedBookView(LoginRequiredMixin, UpdateView):
    model = BookInstance
    form_class = BorrowReservedBookForm
    template_name = "catalog/book_borrow_reserved.html"
    success_url = reverse_lazy("my-borrowed")

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            borrow_reserved_book(
                book_instance=self.object,
                user=self.request.user,
                due_back=form.cleaned_data.get("due_back"),
            )
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        return HttpResponseRedirect(self.get_success_url())


class BorrowOrReserveBookView(LoginRequiredMixin, View):
    template_name = "catalog/bookinstance_form.html"

    def get_object(self) -> BookInstance:
        return get_object_or_404(BookInstance, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs) -> HttpResponse:
        instance = self.get_object()
        form = BorrowOrReserveBookForm()
        return render(request, self.template_name, {"form": form, "object": instance})

    def post(self, request, *args, **kwargs) -> HttpResponseRedirect:
        instance = self.get_object()
        form = BorrowOrReserveBookForm(request.POST)
        if form.is_valid():
            try:
                borrow_or_reserve_book(
                    book_instance=instance,
                    user=request.user,
                    due_back=form.cleaned_data.get("due_back"),
                    status=form.cleaned_data.get("status"),
                )
            except ValueError as e:
                form.add_error(None, str(e))
                return render(request, self.template_name, {"form": form, "object": instance})
            return redirect("my-borrowed")
        return render(request, self.template_name, {"form": form, "object": instance})


class ChangeBookStatusView(PermissionRequiredMixin, UpdateView):
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
def return_book_view(request, pk: uuid4) -> None:
    instance = get_object_or_404(BookInstance, pk=pk)

    try:
        return_book(book_instance=instance)
        messages.success(request, f"Book '{instance.book.title}' ({instance.id}) successfuly returned.")
    except Exception as e:
        messages.error(request, f"Error during returning: {e}")

    return redirect("all-borrowed")
