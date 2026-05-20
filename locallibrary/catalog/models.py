import uuid
from datetime import date

from catalog.choices import InstanceStatus, LoanStatus
from utils.image_processing import ImageProcessingMixin, GeneratePath
from utils.validators import validate_file_size

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib import admin
from django.db import models
from django.db.models import UniqueConstraint, Q, CheckConstraint, F
from django.db.models.functions import Lower
from django.urls import reverse

from catalog.managers import BookInstanceManager

class Genre(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("name"),
                name="genre_name_case_insensitive_unique",
                violation_error_message="Genre already exists (case insensitive match)",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("name"),
                name="language_name_case_insensitive_unique",
                violation_error_message="Language already exists (case insensitive match)",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Book(ImageProcessingMixin, models.Model):
    IMAGE_SIZE = (600, 350)
    title = models.CharField(max_length=200)
    author = models.ForeignKey("catalog.Author", on_delete=models.PROTECT, null=True, related_name="books")
    summary = models.TextField(max_length=1000, help_text="Enter a brief description of the book")
    isbn = models.CharField(
        "ISBN",
        max_length=13,
        unique=True,
        help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn">' \
        'ISBN number'
        '</a>',
    )
    genre = models.ManyToManyField(
        "catalog.Genre", help_text="Select a genre for this book", related_name="books"
    )
    language = models.ForeignKey(
        "catalog.Language",
        help_text="Select a language for this book",
        on_delete=models.PROTECT,
        related_name="books",
    )
    image = models.ImageField(
        upload_to=GeneratePath("book"),
        blank=True,
        null=True,
        max_length=300,
        validators=[
            validate_file_size,
            FileExtensionValidator(
                allowed_extensions=["jpeg", "png", "webp", "jpg", "svg"], message="Invalid file extension"
            ),
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_image = self.image.name if self.image else None

    def __str__(self) -> str:
        return str(self.title)

    def get_absolute_url(self) -> str:
        return reverse("book-detail", args=[str(self.id)])

    @admin.display(description="Genre")
    def display_genre(self) -> str:
        return ", ".join(genre.name for genre in self.genre.all()[:3])



class BookInstance(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique ID for this particular book across whole library",
        editable=False,
    )
    book = models.ForeignKey("catalog.Book", on_delete=models.PROTECT, related_name="instances")
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True, help_text="Date when book should become available")
    status = models.CharField(
        choices=InstanceStatus.choices,
        max_length=20,
        default=InstanceStatus.MAINTENANCE,
        help_text="Book availability",
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="borrowed_books",
    )

    objects: BookInstanceManager = BookInstanceManager()

    class Meta:
        ordering = ["due_back"]
        permissions = (
            ("can_mark_returned", "Set book as returned"),
            ("can_change_due_back", "Set due back date"),
        )
        constraints = [
                CheckConstraint(
                    condition=(
                        ~Q(status__in=[InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]) 
                        | 
                        (Q(due_back__isnull=False) & Q(borrower__isnull=False))
                    ),
                    name='check_due_back_and_borrower_if_on_loan_or_reserved',
                    violation_error_message="Due back date and borrower cannot be empty when book is on loan or reserved."
                )
        ]
        indexes = [models.Index(fields=["borrower"]), models.Index(fields=["book"])]

    def __str__(self) -> str:
        return f"{self.id} ({self.book.title})"
    
    @property
    def is_overdue(self) -> bool:
        return bool(self.due_back and date.today() > self.due_back)



class Author(ImageProcessingMixin, models.Model):
    IMAGE_SIZE = (500, 400)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField("born", null=True, blank=True)
    date_of_death = models.DateField("died", null=True, blank=True)
    image = models.ImageField(
        upload_to=GeneratePath("authors"),
        blank=True,
        null=True,
        max_length=300,
        validators=[
            validate_file_size,
            FileExtensionValidator(
                allowed_extensions=["jpeg", "png", "webp", "jpg", "svg"], message="Invalid file extension"
            ),
            
        ]
    )
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_image = self.image.name if self.image else None

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            CheckConstraint(
                condition=Q(date_of_birth__isnull=True) 
                    | Q(date_of_death__isnull=True) 
                    | Q(date_of_birth__lte=F("date_of_death")),
                name="check_birth_before_death",
                violation_error_message="Author could not die earlier than was born!"
            )
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self) -> str:
        return reverse("author-detail", args=[str(self.id)])

    def clean(self) -> None:
        super().clean()
        if self.date_of_death and self.date_of_birth:
            if self.date_of_birth > self.date_of_death:
                raise ValidationError("Author could not die earlier than was born!")


class Loan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="loans")
    book_instance = models.ForeignKey(
        "catalog.BookInstance", on_delete=models.PROTECT, related_name="loans"
    )

    issued_at = models.DateField(auto_now_add=True)
    returned_at = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.ACTIVE)

    @property
    def is_overdue(self) -> bool:
        return self.overdue_days > 0
    
    @property
    def overdue_days(self) -> int:
        end_date = self.returned_at if self.returned_at else date.today()
     
        if not self.book_instance.due_back or end_date <= self.book_instance.due_back:
            return 0
            
        return (end_date - self.book_instance.due_back).days

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "borrower",
                ]
            )
        ]

    def __str__(self):
        return f'{self.borrower.first_name} {self.borrower.last_name}, loan status: {self.status}'
