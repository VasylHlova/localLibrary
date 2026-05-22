from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from catalog.choices import InstanceStatus
from catalog.tests.helper.factories import (
    AvailableBookInstanceFactory,
    LoanFactory,
    OnLoanBookInstanceFactory,
    ReservedBookInstanceFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


class TestBookActionBorrowOrReserveIntegration:
    def test_anonymous_forbidden(self, api_client):
        instance = AvailableBookInstanceFactory()
        response = api_client.post(
            reverse("api-instance-action-borrow-or-reserve", args=[instance.pk]),
            {"status": InstanceStatus.ON_LOAN, "due_back": str(date.today() + timedelta(days=7))},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_borrow_available_book(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = AvailableBookInstanceFactory()
        payload = {
            "status": InstanceStatus.ON_LOAN,
            "due_back": str(date.today() + timedelta(days=7)),
        }
        response = api_client.post(
            reverse("api-instance-action-borrow-or-reserve", args=[instance.pk]),
            payload,
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.status == InstanceStatus.ON_LOAN
        assert instance.borrower == user

    def test_reserve_available_book(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = AvailableBookInstanceFactory()
        payload = {
            "status": InstanceStatus.RESERVED,
            "due_back": str(date.today() + timedelta(days=7)),
        }
        response = api_client.post(
            reverse("api-instance-action-borrow-or-reserve", args=[instance.pk]),
            payload,
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.status == InstanceStatus.RESERVED


class TestBookActionBorrowOrReserveUnit:
    def test_invalid_serializer_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = AvailableBookInstanceFactory()
        response = api_client.post(
            reverse("api-instance-action-borrow-or-reserve", args=[instance.pk]),
            {},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("catalog.api.views.borrow_or_reserve_book")
    def test_service_raises_value_error_returns_400(self, mock_service, api_client):
        mock_service.side_effect = ValueError("Book is not available")
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = AvailableBookInstanceFactory()
        payload = {
            "status": InstanceStatus.ON_LOAN,
            "due_back": str(date.today() + timedelta(days=7)),
        }
        response = api_client.post(
            reverse("api-instance-action-borrow-or-reserve", args=[instance.pk]),
            payload,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Book is not available" in response.data["detail"]


class TestBookActionBorrowReservedIntegration:
    def test_anonymous_forbidden(self, api_client):
        instance = ReservedBookInstanceFactory()
        response = api_client.post(
            reverse("api-instance-action-borrow-reserved", args=[instance.pk]),
            {"due_back": str(date.today() + timedelta(days=7))},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_borrow_reserved_success(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = ReservedBookInstanceFactory(borrower=user)
        payload = {"due_back": str(date.today() + timedelta(days=7))}
        response = api_client.post(
            reverse("api-instance-action-borrow-reserved", args=[instance.pk]),
            payload,
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.status == InstanceStatus.ON_LOAN


class TestBookActionBorrowReservedUnit:
    def test_invalid_serializer_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = ReservedBookInstanceFactory(borrower=user)
        response = api_client.post(
            reverse("api-instance-action-borrow-reserved", args=[instance.pk]),
            {},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("catalog.api.views.borrow_reserved_book")
    def test_service_raises_value_error_returns_400(self, mock_service, api_client):
        mock_service.side_effect = ValueError("You are not the one who reserved this book.")
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = ReservedBookInstanceFactory(borrower=user)
        payload = {"due_back": str(date.today() + timedelta(days=7))}
        response = api_client.post(
            reverse("api-instance-action-borrow-reserved", args=[instance.pk]),
            payload,
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "reserved" in response.data["detail"].lower()


class TestBookActionReturnBookIntegration:
    def test_anonymous_forbidden(self, api_client):
        instance = OnLoanBookInstanceFactory()
        response = api_client.post(
            reverse("api-instance-action-return-book", args=[instance.pk]),
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_can_mark_returned(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = OnLoanBookInstanceFactory(borrower=user)
        response = api_client.post(
            reverse("api-instance-action-return-book", args=[instance.pk]),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_return_book_success(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        instance = OnLoanBookInstanceFactory()
        LoanFactory(book_instance=instance, borrower=instance.borrower)
        response = api_client.post(
            reverse("api-instance-action-return-book", args=[instance.pk]),
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.status == InstanceStatus.AVAILABLE


class TestBookActionReturnBookUnit:
    @patch("catalog.api.views.return_book")
    def test_service_raises_value_error_returns_400(self, mock_service, api_client, staff_user):
        mock_service.side_effect = ValueError("Bad status")
        api_client.force_authenticate(user=staff_user)
        instance = AvailableBookInstanceFactory()
        response = api_client.post(
            reverse("api-instance-action-return-book", args=[instance.pk]),
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Bad status" in response.data["detail"]


class TestBookActionExtendLoanIntegration:
    def test_anonymous_forbidden(self, api_client):
        instance = OnLoanBookInstanceFactory()
        response = api_client.patch(
            reverse("api-instance-action-extend-loan", args=[instance.pk]),
            {"due_back": str(date.today() + timedelta(days=14))},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_requires_can_change_due_back(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        instance = OnLoanBookInstanceFactory(borrower=user)
        response = api_client.patch(
            reverse("api-instance-action-extend-loan", args=[instance.pk]),
            {"due_back": str(date.today() + timedelta(days=14))},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_extend_loan_success(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        new_due = date.today() + timedelta(days=14)
        instance = OnLoanBookInstanceFactory()
        response = api_client.patch(
            reverse("api-instance-action-extend-loan", args=[instance.pk]),
            {"due_back": str(new_due)},
        )
        assert response.status_code == status.HTTP_200_OK
        instance.refresh_from_db()
        assert instance.due_back == new_due


class TestBookActionExtendLoanUnit:
    def test_invalid_serializer_returns_400(self, api_client, staff_user):
        api_client.force_authenticate(user=staff_user)
        instance = OnLoanBookInstanceFactory()
        response = api_client.patch(
            reverse("api-instance-action-extend-loan", args=[instance.pk]),
            {},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("catalog.api.views.renew_book")
    def test_service_raises_value_error_returns_400(self, mock_service, api_client, staff_user):
        mock_service.side_effect = ValueError("Bad status for renew")
        api_client.force_authenticate(user=staff_user)
        instance = OnLoanBookInstanceFactory()
        response = api_client.patch(
            reverse("api-instance-action-extend-loan", args=[instance.pk]),
            {"due_back": str(date.today() + timedelta(days=14))},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Bad status for renew" in response.data["detail"]
