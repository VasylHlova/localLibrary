from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None, **extra_fields: Any) -> Any:
        if not email:
            raise ValueError(_("Email must be set"))

        email = self.normalize_email(email)
        from typing import cast

        from django.contrib.auth.models import AbstractBaseUser

        user = cast(AbstractBaseUser, self.model(email=email, **extra_fields))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)
