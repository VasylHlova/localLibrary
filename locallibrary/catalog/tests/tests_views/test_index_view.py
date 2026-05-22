from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from catalog.choices import InstanceStatus
from catalog.models import Author, Book, BookInstance
from catalog.tests.helper.factories import (
    AuthorFactory,
    AvailableBookInstanceFactory,
    BookFactory,
    OnLoanBookInstanceFactory,
)


class IndexViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        AuthorFactory.create_batch(2)
        BookFactory.create_batch(3)

        AvailableBookInstanceFactory.create_batch(3)
        OnLoanBookInstanceFactory.create_batch(1)

    def test_view_url_and_template_are_correct(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "index.html")

    def test_context_data_contains_exact_counts(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.context["num_authors"], Author.objects.count())
        self.assertEqual(response.context["num_books"], Book.objects.count())
        self.assertEqual(response.context["num_instances"], BookInstance.objects.count())
        self.assertEqual(
            response.context["num_instances_available"],
            BookInstance.objects.filter(status=InstanceStatus.AVAILABLE).count(),
        )

    def test_session_num_visits_increments_correctly(self):
        response1 = self.client.get(reverse("index"))
        self.assertEqual(response1.context["num_visits"], 1)

        response2 = self.client.get(reverse("index"))
        self.assertEqual(response2.context["num_visits"], 2)

        response3 = self.client.get(reverse("index"))
        self.assertEqual(response3.context["num_visits"], 3)

        self.assertEqual(self.client.session["num_visits"], 3)
