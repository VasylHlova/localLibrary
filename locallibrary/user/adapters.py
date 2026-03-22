from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.contrib.auth import get_user_model
from django.http import HttpRequest


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request: HttpRequest, sociallogin: SocialLogin) -> None:
        User = get_user_model()

        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get("email")

        if email:
            try:
                user = User.objects.get(email=email)

                sociallogin.connect(request, user)

            except User.DoesNotExist:
                pass
