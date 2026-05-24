from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from user.tests.helper.factories import ProfileFactory, UserFactory


class UserDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = UserFactory()
        cls.owner_profile = ProfileFactory(user=cls.owner)
        cls.other_user = UserFactory()
        cls.other_profile = ProfileFactory(user=cls.other_user)

        cls.url = reverse("user-detail", kwargs={"pk": cls.owner.pk})

    def test_redirects_to_login_if_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_view_url_accessible_by_name_and_uses_correct_template(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "user/customuser_detail.html")

    def test_context_is_owner_is_true_for_own_profile(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)

        self.assertTrue(response.context["is_owner"])

    def test_context_is_owner_is_false_for_other_profile(self):
        from django.contrib.auth.models import Permission

        permission = Permission.objects.get(codename="view_customuser")
        self.other_user.user_permissions.add(permission)
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)

        self.assertFalse(response.context["is_owner"])


class UpdateUserProfileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.profile = ProfileFactory(user=cls.user)

        cls.url = reverse("profile-edit", kwargs={"pk": cls.user.pk})

    def test_redirects_to_login_if_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_view_url_accessible_by_name_and_uses_correct_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "user/edit_profile.html")

    def test_post_valid_data_redirects_to_user_detail(self):
        self.client.force_login(self.user)
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }
        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("user-detail", kwargs={"pk": self.user.pk}))
