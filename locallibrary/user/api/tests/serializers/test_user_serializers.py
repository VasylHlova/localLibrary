from datetime import date, timedelta

import pytest
from rest_framework.test import APIRequestFactory
from user.api.serializers import (
    UserDetailSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserProfileWriteSerializer,
    UserShortSerializer,
    UserWriteSerializer,
)
from user.tests.helper.factories import ProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_user_short_serializer():
    user = UserFactory()
    factory = APIRequestFactory()
    request = factory.get("/api/users/")
    serializer = UserShortSerializer(instance=user, context={"request": request})
    assert serializer.data["first_name"] == user.first_name
    assert serializer.data["last_name"] == user.last_name
    assert "detail_url" in serializer.data


def test_user_profile_serializer():
    profile = ProfileFactory()
    profile.role = "user"
    profile.date_of_birth = "1990-01-01"
    profile.save()
    serializer = UserProfileSerializer(instance=profile)
    assert serializer.data["role"] == "user"
    assert serializer.data["date_of_birth"] == "1990-01-01"


def test_user_list_serializer():
    user = UserFactory()
    serializer = UserListSerializer(instance=user)
    assert serializer.data["first_name"] == user.first_name
    assert serializer.data["email"] == user.email


def test_user_detail_serializer():
    user = UserFactory()
    profile = user.profile
    profile.role = "admin"
    profile.save()
    serializer = UserDetailSerializer(instance=user)
    assert serializer.data["username"] == user.username
    assert serializer.data["profile"]["role"] == "admin"


def test_user_write_serializer_create():
    data = {
        "first_name": "New",
        "last_name": "User",
        "email": "newuser@gmail.com",
        "username": "newuser",
        "password": "securepassword",
    }
    serializer = UserWriteSerializer(data=data)
    assert serializer.is_valid()
    user = serializer.save()
    assert user.first_name == "New"
    assert user.check_password("securepassword")


def test_user_write_serializer_update():
    user = UserFactory()
    data = {
        "first_name": "Updated",
    }
    serializer = UserWriteSerializer(instance=user, data=data, partial=True)
    assert serializer.is_valid()
    updated_user = serializer.save()
    assert updated_user.first_name == "Updated"


def test_user_profile_write_serializer_valid():
    profile = ProfileFactory()
    data = {"date_of_birth": "1990-01-01"}
    serializer = UserProfileWriteSerializer(instance=profile, data=data, partial=True)
    assert serializer.is_valid()


def test_user_profile_write_serializer_invalid_age():
    profile = ProfileFactory()
    data = {"date_of_birth": str(date.today() - timedelta(days=365))}
    serializer = UserProfileWriteSerializer(instance=profile, data=data, partial=True)
    assert not serializer.is_valid()
    assert "date_of_birth" in serializer.errors
