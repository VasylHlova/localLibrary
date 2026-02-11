from django.db import models
from django.utils.translation import gettext_lazy as _

class InstanceStatus(models.TextChoices):
    MAINTENANCE = 'm', _('Maintenance')
    ON_LOAN = 'o', _('On loan')
    AVAILABLE = 'a', _('Available')
    RESERVED = 'r', _('Reserved') 

class LoanStatus(models.TextChoices):
    ACTIVE = 'a', _('Active')
    RETURNED = 'r', _('Returned')