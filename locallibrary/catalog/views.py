import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages

from .models import Book, Author, BookInstance, Genre, Language
from .forms  import RenewBookForm,  BorrowOrReserveBookForm

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
    
@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':

        form = RenewBookForm(request.POST)

        if form.is_valid():
            
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))
        
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)

        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death', 'photo']
    initial = {'date_of_birth': '31.12.2020'}
    permission_required = 'catalog.add_author'
    
class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__'
    permission_required = 'catalog.change_author'
    
class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'
    
    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse('author-delete', kwargs={'pk':self.object.pk})
            )
        
class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'photo']
    permission_required = 'catalog.create_book'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = '__all__'
    permission_required = 'catalog.update_book'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception as e:
            return HttpResponseRedirect(
                reverse('book-delete', kwargs={'pk': self.object.pk})
            )
        
class BorrowOrReserveBook(LoginRequiredMixin, UpdateView):

    model = BookInstance
    form_class = BorrowOrReserveBookForm
    

    def dispatch(self, request, *args, **kwargs):

        book_inst = self.get_object()

        if book_inst.status != 'a':
            messages.error(request, 'This instance is not avaliable!')
            return redirect('book-detail', pk=book_inst.book.id)

        return super().dispatch(request, *args, **kwargs)

    
    def form_valid(self, form):

        form.instance.borrower = self.request.user

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('my-borrowed')

class ChangeBookStatus(PermissionRequiredMixin, UpdateView):
    model = BookInstance
    fields = {'status'}
    permission_required = ['catalog.can_mark_returned', 'catalog.update_bookinstance']
    template_name = 'catalog/book_change_status.html'
    success_url = reverse_lazy('all-borrowed')