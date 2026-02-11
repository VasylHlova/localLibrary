from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.base import File

from .utils import InstanceStatus

import datetime 


def validate_file_size(file:File) -> None:
    limit = 20 * 1024 * 1024

    if file.size > limit :
        raise ValidationError('Exceeded max file size(20MB)')
    
def validate_future_date(value:datetime.date) -> None:
    if value < datetime.date.today():
        raise ValidationError(_('Invalid date - renewal in past!'))

def validate_term_limit(value:datetime.date, status:str=InstanceStatus.ON_LOAN) -> None:
    weeks = 4 if status == InstanceStatus.ON_LOAN else 1
    if value > datetime.date.today() + datetime.timedelta(weeks=weeks):
        raise ValidationError(_(f'Invalid date - renewal more than {weeks} weeks ahead!'))
    
