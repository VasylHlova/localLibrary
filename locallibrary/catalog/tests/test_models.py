from datetime import date

from django.test import TestCase
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS

from catalog.models import Genre, Language
from catalog.tests.helper.factories import (
    AuthorFactory,
    GenreFactory,
    LanguageFactory,
    BookFactory,
    AvailableBookInstanceFactory,
    OnLoanBookInstanceFactory,
    OverdueBookInstanceFactory,
    LoanFactory,
    ImageFactory,
)


class AuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = AuthorFactory()

    def test_first_name_label_is_correct(self):
        field_label = self.author._meta.get_field("first_name").verbose_name
        self.assertEqual(field_label, "first name")

    def test_date_of_death_label_is_correct(self):
        field_label = self.author._meta.get_field("date_of_death").verbose_name
        self.assertEqual(field_label, "died")

    def test_date_of_birth_label_is_correct(self):
        field_label = self.author._meta.get_field("date_of_birth").verbose_name
        self.assertEqual(field_label, "born")

    def test_first_name_max_length_is_100(self):
        max_length = self.author._meta.get_field("first_name").max_length
        self.assertEqual(max_length, 100)

    def test_str_returns_first_name_and_last_name(self):
        expected = f"{self.author.first_name} {self.author.last_name}"
        self.assertEqual(str(self.author), expected)

    def test_get_absolute_url_returns_correct_url(self):
        self.assertEqual(self.author.get_absolute_url(), f"/catalog/author/{self.author.pk}")

    def test_full_clean_raises_error_when_death_date_earlier_than_birth_date(self):
        author = AuthorFactory(
            date_of_birth=date(1999, 12, 31),
            date_of_death=date(1999, 12, 30),
        )

        with self.assertRaises(ValidationError) as context:
            author.full_clean()

        errors = context.exception.message_dict
        self.assertIn(NON_FIELD_ERRORS, errors)
        self.assertEqual(
            errors[NON_FIELD_ERRORS][0],
            "Author could not die earlier than was born!",
        )

    def test_full_clean_passes_when_birth_and_death_dates_are_valid(self):
        author = AuthorFactory(
            date_of_birth=date(1999, 12, 31),
            date_of_death=date(2000, 1, 1),
        )
        author.full_clean()

    def test_full_clean_passes_when_image_has_valid_extension(self):
        for ext, fmt, content_type in [
            ("jpg", "JPEG", "image/jpeg"),
            ("jpeg", "JPEG", "image/jpeg"),
            ("png", "PNG", "image/png"),
            ("webp", "WEBP", "image/webp"),
        ]:
            with self.subTest(ext=ext):
                author = AuthorFactory.build(
                    image=ImageFactory.create(name=f"test.{ext}", format=fmt, content_type=content_type)
                )
                author.full_clean()

    def test_full_clean_raises_error_when_image_has_invalid_extension(self):
        author = AuthorFactory.build(image=ImageFactory.create_invalid_extension())

        with self.assertRaises(ValidationError) as context:
            author.full_clean()

        self.assertIn("image", context.exception.message_dict)
        self.assertIn("Invalid file extension", context.exception.message_dict["image"][0])

    def test_full_clean_raises_error_when_image_exceeds_max_size(self):
        author = AuthorFactory.build(image=ImageFactory.create_oversized())

        with self.assertRaises(ValidationError) as context:
            author.full_clean()

        self.assertIn("image", context.exception.message_dict)
        self.assertIn("Exceeded max file size(20MB)", context.exception.message_dict["image"])
        
    def test_full_clean_passes_when_image_is_none(self):
        author = AuthorFactory.build(image=None)
        author.full_clean()


class BookModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        genres = GenreFactory.create_batch(4)
        cls.book = BookFactory(genre=genres)

    def test_title_max_length_is_200(self):
        max_length = self.book._meta.get_field("title").max_length
        self.assertEqual(max_length, 200)

    def test_summary_help_text_is_correct(self):
        help_text = self.book._meta.get_field("summary").help_text
        self.assertEqual(help_text, "Enter a brief description of the book")

    def test_isbn_max_length_is_13(self):
        max_length = self.book._meta.get_field("isbn").max_length
        self.assertEqual(max_length, 13)

    def test_isbn_help_text_is_correct(self):
        help_text = self.book._meta.get_field("isbn").help_text
        self.assertEqual(
            help_text,
            '13 Character <a href="https://www.isbn-international.org/content/what-isbn">'
            "ISBN number"
            "</a>",
        )

    def test_genre_help_text_is_correct(self):
        help_text = self.book._meta.get_field("genre").help_text
        self.assertEqual(help_text, "Select a genre for this book")

    def test_language_help_text_is_correct(self):
        help_text = self.book._meta.get_field("language").help_text
        self.assertEqual(help_text, "Select a language for this book")

    def test_str_returns_book_title(self):
        self.assertEqual(str(self.book), self.book.title)

    def test_get_absolute_url_returns_correct_url(self):
        self.assertEqual(self.book.get_absolute_url(), f"/catalog/book/{self.book.pk}")

    def test_display_genre_returns_max_three_genres(self):
        result = self.book.display_genre()
        self.assertEqual(len(result.split(", ")), 3)

    def test_full_clean_passes_when_image_has_valid_extension(self):
        author = AuthorFactory()
        language = LanguageFactory()
        
        for ext, fmt, content_type in [
            ("jpg", "JPEG", "image/jpeg"),
            ("jpeg", "JPEG", "image/jpeg"),
            ("png", "PNG", "image/png"),
            ("webp", "WEBP", "image/webp"),
        ]:
            with self.subTest(ext=ext):
                book = BookFactory.build(
                    author=author,
                    language=language,
                    image=ImageFactory.create(name=f"test.{ext}", format=fmt, content_type=content_type)
                )
                book.full_clean()

    def test_full_clean_raises_error_when_image_has_invalid_extension(self):
        book = BookFactory.build(
            author=AuthorFactory(),
            language=LanguageFactory(),
            image=ImageFactory.create_invalid_extension()
        )

        with self.assertRaises(ValidationError) as context:
            book.full_clean()

        self.assertIn("image", context.exception.message_dict)
        self.assertIn("Invalid file extension", context.exception.message_dict["image"][0])

    def test_full_clean_raises_error_when_image_exceeds_max_size(self):
        book = BookFactory.build(
            author=AuthorFactory(),
            language=LanguageFactory(),
            image=ImageFactory.create_oversized()
        )

        with self.assertRaises(ValidationError) as context:
            book.full_clean()

        self.assertIn("image", context.exception.message_dict)
        self.assertIn("Exceeded max file size(20MB)", context.exception.message_dict["image"])

    def test_full_clean_passes_when_image_is_none(self):
        book = BookFactory.build(
            author=AuthorFactory(),
            language=LanguageFactory(),
            image=None
        )
        book.full_clean()


class GenreModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.genre = GenreFactory(name="Test genre")

    def test_name_max_length_is_200(self):
        max_length = self.genre._meta.get_field("name").max_length
        self.assertEqual(max_length, 200)

    def test_name_help_text_is_correct(self):
        help_text = self.genre._meta.get_field("name").help_text
        self.assertEqual(help_text, "Enter a book genre (e.g. Science Fiction, French Poetry etc.)")

    def test_full_clean_raises_error_when_genre_name_already_exists(self):
        with self.assertRaises(ValidationError) as context:
            duplicate = Genre(name="test genre") 
            duplicate.full_clean()

        errors = context.exception.message_dict
        self.assertIn(NON_FIELD_ERRORS, errors)
        self.assertEqual(
            errors[NON_FIELD_ERRORS][0],
            "Genre already exists (case insensitive match)",
        )

    def test_str_returns_genre_name(self):
        self.assertEqual(str(self.genre), self.genre.name)


class LanguageModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language = LanguageFactory(name="Test language")

    def test_name_max_length_is_100(self):
        max_length = self.language._meta.get_field("name").max_length
        self.assertEqual(max_length, 100)

    def test_full_clean_raises_error_when_language_name_already_exists(self):
        with self.assertRaises(ValidationError) as context:
            duplicate = Language(name="test language")
            duplicate.full_clean()

        errors = context.exception.message_dict
        self.assertIn(NON_FIELD_ERRORS, errors)
        self.assertEqual(
            errors[NON_FIELD_ERRORS][0],
            "Language already exists (case insensitive match)",
        )

    def test_str_returns_language_name(self):
        self.assertEqual(str(self.language), self.language.name)


class BookInstanceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.available_instance = AvailableBookInstanceFactory()
        cls.on_loan_instance = OnLoanBookInstanceFactory()
        cls.overdue_instance = OverdueBookInstanceFactory()

    def test_id_help_text_is_correct(self):
        help_text = self.available_instance._meta.get_field("id").help_text
        self.assertEqual(help_text, "Unique ID for this particular book across whole library")

    def test_imprint_max_length_is_200(self):
        max_length = self.available_instance._meta.get_field("imprint").max_length
        self.assertEqual(max_length, 200)

    def test_due_back_help_text_is_correct(self):
        help_text = self.available_instance._meta.get_field("due_back").help_text
        self.assertEqual(help_text, "Date when book should become available")

    def test_status_max_length_is_20(self):
        max_length = self.available_instance._meta.get_field("status").max_length
        self.assertEqual(max_length, 20)

    def test_status_help_text_is_correct(self):
        help_text = self.available_instance._meta.get_field("status").help_text
        self.assertEqual(help_text, "Book availability")

    def test_str_returns_id_and_book_title(self):
        expected = f"{self.available_instance.id} ({self.available_instance.book.title})"
        self.assertEqual(str(self.available_instance), expected)

    def test_is_overdue_returns_true_when_due_back_in_the_past(self):
        self.assertTrue(self.overdue_instance.is_overdue)

    def test_is_overdue_returns_false_when_due_back_in_the_future(self):
        self.assertFalse(self.on_loan_instance.is_overdue)

    def test_is_overdue_returns_false_when_due_back_is_none(self):
        self.assertFalse(self.available_instance.is_overdue)


class LoanModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.loan = LoanFactory()

    def test_status_max_length_is_20(self):
        max_length = self.loan._meta.get_field("status").max_length
        self.assertEqual(max_length, 20)

    def test_str_returns_borrower_full_name_and_loan_status(self):
        expected = f"{self.loan.borrower.first_name} {self.loan.borrower.last_name}, loan status: {self.loan.status}"
        self.assertEqual(str(self.loan), expected)
