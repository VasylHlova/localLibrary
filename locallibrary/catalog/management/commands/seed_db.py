import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from catalog.models import Book, Author, Genre, Language, BookInstance
from user.models import CustomUser
from utils.choices import InstanceStatus

class Command(BaseCommand):
    help = 'Fill DB with fake data for dev-env'

    def handle(self, *args, **kwargs):
        if Book.objects.exists():
            self.stdout.write(self.style.WARNING('DB already has data. Seeding skipped.'))
            return

        fake = Faker()
        self.stdout.write('Starting data generation...')

        languages = [Language.objects.create(name=name) for name in ['Ukrainian', 'English', 'Polish']]
        genres = [Genre.objects.create(name=name) for name in ['Science Fiction', 'Detective', 'Non-fiction', 'Romance', 'Horror']]

        authors = []
        for _ in range(7):
            author = Author.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(minimum_age=30, maximum_age=90),
            )
            authors.append(author)

        users = []
        for i in range(3):
            user = CustomUser.objects.create_user(
                email=f'testuser{i}@example.com',
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            users.append(user)

        books = []
        for _ in range(12):
            book = Book.objects.create(
                title=fake.catch_phrase(),
                author=random.choice(authors),
                summary=fake.text(max_nb_chars=500),
                isbn=fake.isbn13().replace('-', ''),
                language=random.choice(languages)
            )
            book.genre.set(random.sample(genres, random.randint(1, 3)))
            books.append(book)

        for _ in range(35):
            book = random.choice(books)
            status_choice = random.choice([InstanceStatus.AVAILABLE, InstanceStatus.ON_LOAN, InstanceStatus.MAINTENANCE])
            
            borrower = None
            due_back = None
            if status_choice == InstanceStatus.ON_LOAN:
                borrower = random.choice(users)
                due_back = timezone.now().date() + timedelta(days=random.randint(1, 14))

            BookInstance.objects.create(
                book=book,
                imprint=fake.company(),
                status=status_choice,
                borrower=borrower,
                due_back=due_back
            )

        self.stdout.write(self.style.SUCCESS('Database successfully seeded! Created 12 books and 35 instances.'))