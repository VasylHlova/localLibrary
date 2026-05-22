from datetime import date, timedelta

from django.test import TestCase

from user.forms import CustomSignupForm, UpdateUserProfileForm
from user.tests.helper.factories import UserFactory, ProfileFactory


class CustomSignupFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_signup_method_updates_user_fields(self):
        form_data = {"first_name": "TestFirst", "last_name": "TestLast"}
        form = CustomSignupForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        form.signup(request=None, user=self.user)
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.first_name, "TestFirst")
        self.assertEqual(self.user.last_name, "TestLast")


class UpdateUserProfileFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile = ProfileFactory(user__first_name="OldFirst", user__last_name="OldLast")

    def test_form_initializes_with_user_data(self):
        form = UpdateUserProfileForm(instance=self.profile)
        
        self.assertEqual(form.fields["first_name"].initial, "OldFirst")
        self.assertEqual(form.fields["last_name"].initial, "OldLast")

    def test_form_saves_user_and_profile_data(self):
        valid_date = date.today() - timedelta(days=365 * 25)
        form_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "date_of_birth": valid_date,
        }
        form = UpdateUserProfileForm(data=form_data, instance=self.profile)
        
        self.assertTrue(form.is_valid())
        
        saved_profile = form.save()
        self.profile.user.refresh_from_db()
        
        self.assertEqual(self.profile.user.first_name, "UpdatedFirst")
        self.assertEqual(self.profile.user.last_name, "UpdatedLast")
        self.assertEqual(saved_profile.date_of_birth, valid_date)

    def test_clean_date_of_birth_raises_error_for_future_date(self):
        future_date = date.today() + timedelta(days=10)
        form_data = {"date_of_birth": future_date}
        form = UpdateUserProfileForm(data=form_data, instance=self.profile)
        
        self.assertFalse(form.is_valid())
        self.assertIn("date_of_birth", form.errors)