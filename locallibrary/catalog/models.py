from django.db import models
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.exceptions import ValidationError
from django.conf import settings
import uuid
from datetime import date

class Genre(models.Model):
    name = models.CharField(
        max_length=200, 
        unique=True, 
        help_text='Enter a book genre (e.g. Scince Fiction, French Poetry etc.)'
        )
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('genre-default', args=[str(self.id)])
    
    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='genre_name_case_insensitive_unique',
                violation_error_message = "Genre already exists (case insensitive match)"
            ),
        ]

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name  

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='language_name_case_insensitive_unique',
                violation_error_message = "Language already exists (case insensitive match)"
            ),
        ]

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.RESTRICT, null=True)
    summary = models.TextField(max_length=1000, help_text='Enter a brief description of the book')
    isbn = models.CharField('ISBN', max_length=13, unique=True, help_text='13 Character <a href="https://www.isbn-international.org/content/what-isbn'
                                      '">ISBN number</a>')
    genre = models.ManyToManyField(Genre, help_text='Select a genre for this book')

    def display_genre(self):
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])
    
class BookInstance(models.Model):
    LOAN_STATUS = (
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID for this particular book across whole library')
    book = models.ForeignKey('Book', on_delete=models.RESTRICT, null=True)
    language = models.ForeignKey('Language', help_text='Select a language for this book', on_delete=models.RESTRICT, default=1)
    imprint = models.CharField(max_length=200)
    due_back = models.DateField(null=True, blank=True, help_text='Date when book should become avaliable')
    status = models.CharField(choices=LOAN_STATUS, max_length=1, default='m', help_text='Book availability')

    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)


    @property
    def is_overdue(self):
        return bool(self.due_back and date.today() > self.due_back)
    
    def clean(self):
        super().clean()

        if self.status == 'o' or self.status == 'r':
            if not self.due_back:
                raise ValidationError("Invalid due back date") 
            
    class Meta:
        ordering = ['due_back']
        permissions = (("can_mark_returned", "Set book as returned"),)
        
    def __str__(self):
        return f'{self.id} ({self.book.title})'
    
class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField('born',null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def clean(self):
        
        super().clean()

        if self.date_of_death and self.date_of_birth:
            if self.date_of_birth > self.date_of_death:
                raise ValidationError("Author could not die erlir then was born!!!")