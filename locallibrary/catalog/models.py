from django.db import models
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import FileExtensionValidator

import uuid
from datetime import date
from typing import Optional, Any

from common.file.utils import  GeneratePath
from common.utils import InstanceStatus, LoanStatus
from common.validators import validate_file_size
from common.file.mixins import ImageProcessingMixin

class Genre(models.Model):
    name = models.CharField(
        max_length=200, 
        unique=True, 
        help_text='Enter a book genre (e.g. Science Fiction, French Poetry etc.)'
    )
    
    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='genre_name_case_insensitive_unique',
                violation_error_message="Genre already exists (case insensitive match)"
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)
    
    def get_absolute_url(self) -> str:
        return reverse('genre-default', args=[str(self.id)])
    

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='language_name_case_insensitive_unique',
                violation_error_message="Language already exists (case insensitive match)"
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Book(ImageProcessingMixin, models.Model):
    IMAGE_SIZE = (600, 350)
    title = models.CharField(max_length=200)
    author = models.ForeignKey('catalog.Author', on_delete=models.PROTECT, null=True, related_name='books')
    summary = models.TextField(max_length=1000, help_text='Enter a brief description of the book')
    isbn = models.CharField(
        'ISBN', 
        max_length=13, 
        unique=True, 
        help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">ISBN number</a>'
    )
    genre = models.ManyToManyField('catalog.Genre', help_text='Select a genre for this book', related_name='books')
    language = models.ForeignKey(
        'catalog.Language', 
        help_text='Select a language for this book', 
        on_delete=models.PROTECT, 
        default=1,
        related_name='books'
    )
    photo = models.ImageField(
        upload_to=GeneratePath('book'), 
        blank=True, 
        null=True, 
        max_length=300, 
        validators=[
            validate_file_size,
            FileExtensionValidator(
                allowed_extensions=['jpeg', 'png', 'webp', 'jpg', 'svg'], 
                message='Invalid file extension'
            )
        ]
    )

    def display_genre(self) -> str:
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre' # type: ignore

    def __str__(self) -> str:
        return str(self.title)
    
    def get_absolute_url(self) -> str:
        return reverse('book-detail', args=[str(self.id)])
    
    
class BookInstance(models.Model):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        help_text='Unique ID for this particular book across whole library'
    )
    book = models.ForeignKey('catalog.Book', on_delete=models.PROTECT, null=True, related_name='instances')
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True, help_text='Date when book should become available')
    status = models.CharField(
        choices=InstanceStatus.choices, 
        max_length=1, 
        default=InstanceStatus.MAINTENANCE, 
        help_text='Book availability'
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='borrowed_books'
    )

    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)
        indexes= [
            models.Index(fields=['borrower']),
            models.Index(fields=['book'])
        ]

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_back and date.today() > self.due_back)
    
    @classmethod
    def from_db(cls, db: Optional[str], field_names: list[str], values: list[Any]) -> Any:
        instance = super().from_db(db, field_names, values)
        # Using setattr to avoid type checking issues with dynamic attributes
        setattr(instance, '_loaded_status', instance.status) 
        return instance
    
    def clean(self) -> None:
        super().clean()
        if self.status in (InstanceStatus.ON_LOAN, InstanceStatus.RESERVED):
            if not self.due_back:
                raise ValidationError("Invalid due back date")
            
    def save(self, *args: Any, **kwargs: Any) -> None:
        is_creating = self._state.adding
        old_status: Optional[str] = getattr(self, '_loaded_status', None)
        
        if self.status == InstanceStatus.AVAILABLE:
            self.due_back = None
            self.borrower = None

        super().save(*args, **kwargs) 

        self._handle_loan_history(is_creating, old_status)
        
        # Update the loaded status after save
        setattr(self, '_loaded_status', self.status)

    def _handle_loan_history(self, is_creating: bool, old_status: Optional[str]) -> None:
        current_status = self.status
        previous_status = old_status

        if is_creating and current_status == InstanceStatus.ON_LOAN:
            self._create_loan_record()
            return

        if not is_creating and current_status != previous_status:
            if previous_status == InstanceStatus.ON_LOAN:
                self._close_active_loan()

            if current_status == InstanceStatus.ON_LOAN:
                self._create_loan_record()

    def _create_loan_record(self) -> None:
        if self.borrower and self.due_back:
            Loan.objects.create(
                book_instance=self,
                borrower=self.borrower,
                due_back=self.due_back,
                status=LoanStatus.ACTIVE
            )

    def _close_active_loan(self) -> None:
        active_loan = Loan.objects.filter(
            book_instance=self,
            returned_at__isnull=True
        ).first()

        if active_loan:
            stored_due_back = active_loan.due_back

            if stored_due_back and date.today() > stored_due_back:
                active_loan.is_overdue = True
                active_loan.overdue_days = (date.today() - stored_due_back).days

            active_loan.status = LoanStatus.RETURNED
            active_loan.returned_at = date.today()
            active_loan.save()
            
    def __str__(self) -> str:
        book_title = self.book.title if self.book else "Unknown Book"
        return f'{self.id} ({book_title})'
    

class Author(ImageProcessingMixin, models.Model):
    IMAGE_SIZE = (500, 400)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField('born', null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)
    photo = models.ImageField(
        upload_to=GeneratePath('authors'), 
        blank=True, 
        null=True, 
        max_length=300, 
        validators=[
            validate_file_size,
            FileExtensionValidator(
                allowed_extensions=['jpeg', 'png', 'webp', 'jpg', 'svg'], 
                message='Invalid file extension'
            )
        ]
    )
    
    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self) -> str:
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'
    
    def clean(self) -> None:
        super().clean()
        if self.date_of_death and self.date_of_birth:
            if self.date_of_birth > self.date_of_death:
                raise ValidationError("Author could not die earlier than was born!")
            
class Loan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='loans')
    book_instance = models.ForeignKey('catalog.BookInstance', on_delete=models.PROTECT, related_name='loans')

    issued_at = models.DateField(auto_now_add=True)
    due_back = models.DateField()
    returned_at = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.ACTIVE)
    is_overdue = models.BooleanField(blank=True, null=True)
    overdue_days = models.IntegerField(blank=True, null=True)

    class Meta:
        indexes= [
            models.Index(fields=['borrower',])
        ]