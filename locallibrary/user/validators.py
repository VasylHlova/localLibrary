import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_user_age(value: datetime.date) -> None:
    user_age = (
        datetime.date.today().year
        - value.year
        - ((datetime.date.today().month, datetime.date.today().day) < (value.month, value.day))
    )

    if user_age > 100 or user_age < 6:
        raise ValidationError(_("Invalid date of birth!"))
