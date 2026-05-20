from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    STAFF = "staff", _("Staff")
    CUSTOMER = "customer", _("Customer")
