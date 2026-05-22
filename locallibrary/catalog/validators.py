import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.choices import InstanceStatus


def validate_future_date(value: datetime.date) -> None:
    if value < datetime.date.today():
        raise ValidationError(_("Invalid date - renewal in past!"))


def validate_term_limit(value: datetime.date, status: str = InstanceStatus.ON_LOAN) -> None:
    weeks = 4 if status == InstanceStatus.ON_LOAN else 2
    if value > datetime.date.today() + datetime.timedelta(weeks=weeks):
        raise ValidationError(
            _("Invalid date - renewal more than %(weeks)s weeks ahead!") % {"weeks": weeks}
        )
