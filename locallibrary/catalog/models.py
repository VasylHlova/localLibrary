import uuid
from datetime import date

from utils.choices import InstanceStatus, LoanStatus
from utils.image_proccess import ImageProcessingMixin
from utils.image_proccess import GeneratePath
from utils.validators import validate_file_size
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction
from django.db.models import UniqueConstraint, Q, CheckConstraint
from django.db.models.functions import Lower
from django.urls import reverse
from user.models import CustomUser


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

    def __str__(self) -> str:
        return str(self.title)

    def get_absolute_url(self) -> str:
        return reverse("book-detail", args=[str(self.id)])

    def display_genre(self) -> str:
        return ", ".join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = "Genre"  # type: ignore



class BookInstance(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique ID for this particular book across whole library",
    )
    book = models.ForeignKey("catalog.Book", on_delete=models.PROTECT, null=True, related_name="instances")
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

    class Meta:
        ordering = ["due_back"]
        permissions = (
            ("can_mark_returned", "Set book as returned"),
            ("can_change_status", "Set any book status"),
        )
        constraints = [
                CheckConstraint(
                    condition=(
                        ~Q(status__in=[InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]) | 
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

    @transaction.atomic
    def borrow_book(self, user: CustomUser, due_back: int, status: InstanceStatus) -> None:
        if status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
            return
        
        self.status = status
        self.borrower = user
        self.due_back = due_back
        self.save()
        
        if status == InstanceStatus.ON_LOAN:
            Loan.objects.create(book_instance=self, borrower=user, status=LoanStatus.ACTIVE)

    @transaction.atomic
    def return_book(self) -> None:
        if self.status not in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
            return
        
        if self.status == InstanceStatus.ON_LOAN:
            active_loan = (
                Loan.objects.filter(book_instance=self, returned_at__isnull=True).select_for_update().first()
            )

            if active_loan:
                active_loan.close_loan()

        self.status = InstanceStatus.AVAILABLE
        self.borrower = None
        self.due_back = None
        self.save()


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
        ],
    )

    class Meta:
        ordering = ["last_name", "first_name"]

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="loans")
    book_instance = models.ForeignKey(
        "catalog.BookInstance", on_delete=models.PROTECT, related_name="loans"
    )

    issued_at = models.DateField(auto_now_add=True)
    returned_at = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.ACTIVE)
    is_overdue = models.BooleanField(blank=True, null=True)
    overdue_days = models.IntegerField(blank=True, null=True)

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

    def close_loan(self) -> None:
        self.status = LoanStatus.RETURNED
        self.returned_at = date.today()

        if self.book_instance.due_back < self.returned_at:
            delta = self.returned_at - self.book_instance.due_back

            self.is_overdue = True
            self.overdue_days = delta.days
        else:
            self.is_overdue = False

        self.save()
