from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Book, Author, BookInstance, Genre, Language


def index(request):

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.filter(status__exact='a').count()


    num_authors = Author.objects.count()
    num_visits = request.session.get('num_visits', 0)

    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(ListView):

    model = Book
    paginate_by = 10

class AuthorListView(ListView):

    model = Author
    paginate_by = 10

class BookDetailView(DetailView):
    model = Book

class AuthorDetailView(DetailView):
    model = Author

class LoanBookByUserListView(LoginRequiredMixin, ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )

class LoanBookListView(PermissionRequiredMixin, ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed.html'
    permission_required = 'catalog.can_mark_returned', 'catalog.view_bookinstance'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(status__exact='o')
            .order_by('due_back')
        )