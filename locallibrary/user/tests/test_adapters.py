from unittest.mock import MagicMock

from django.test import TestCase
from django.http import HttpRequest

from user.adapters import MySocialAccountAdapter
from .helper.factories import UserFactory




class MySocialAccountAdapterTest(TestCase):
    def setUp(self):
        self.adapter = MySocialAccountAdapter()
        self.request = HttpRequest()
        self.sociallogin = MagicMock()
        self.sociallogin.account.extra_data = {}

    def test_pre_social_login_returns_early_if_sociallogin_is_existing(self):
        self.sociallogin.is_existing = True
        
        self.adapter.pre_social_login(self.request, self.sociallogin)
        
        self.sociallogin.connect.assert_not_called()

    def test_pre_social_login_connects_user_if_email_exists_in_db(self):
        user = UserFactory(email="existing@mail.com")
        self.sociallogin.is_existing = False
        self.sociallogin.account.extra_data = {"email": "existing@mail.com"}
        
        self.adapter.pre_social_login(self.request, self.sociallogin)
        
        self.sociallogin.connect.assert_called_once_with(self.request, user)

    def test_pre_social_login_does_not_connect_if_user_does_not_exist(self):
        self.sociallogin.is_existing = False
        self.sociallogin.account.extra_data = {"email": "nonexistent@mail.com"}
        
        self.adapter.pre_social_login(self.request, self.sociallogin)
        
        self.sociallogin.connect.assert_not_called()

    def test_pre_social_login_does_not_connect_if_no_email_in_extra_data(self):
        self.sociallogin.is_existing = False
        self.sociallogin.account.extra_data = {}
        
        self.adapter.pre_social_login(self.request, self.sociallogin)
        
        self.sociallogin.connect.assert_not_called()