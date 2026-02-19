from  django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BookInstance
from common.validators import validate_future_date, validate_term_limit
from common.choices import InstanceStatus

from typing import Any

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text='Enter a date between now and 4 weeks (default 3).',
                                   validators=[validate_future_date, validate_term_limit])
    
class BaseBookInstanceForm(forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = ['status', 'due_back']

    def __init__(self, *args:Any, **kwargs:Any) -> None:
        super().__init__(*args, **kwargs)

        self.fields['due_back'].validators.append(validate_future_date)

    def clean(self):
        cleaned_data = super().clean()
        
        status_data = self.cleaned_data.get('status')
        due_back_data = self.cleaned_data.get('due_back')
        
        if status_data and due_back_data:
            if status_data in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
                try:
                    validate_term_limit(due_back_data, status=status_data)
                except ValidationError as e:
                    self.add_error('due_back', e)

        return cleaned_data        

class BorrowOrReserveBookForm(BaseBookInstanceForm):
    STATUS_CHOICES = (
                        (InstanceStatus.ON_LOAN, 'Borrow'),
                        (InstanceStatus.RESERVED, 'Reserve'),
                    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, label='What do you wish?', widget=forms.RadioSelect)

    class Meta(BaseBookInstanceForm.Meta):
        widgets = {
            'due_back': forms.DateInput(attrs={'placeholder': '1999-12-31',})
        }
    
    def clean(self) -> dict:
        cleaned_data = super().clean()

        if self.instance.pk:
            current_status = BookInstance.objects.values_list('status', flat=True).get(pk=self.instance.pk)
            if current_status and current_status != InstanceStatus.AVAILABLE:
                raise ValidationError(_('This book is not available!'))
                            
        return cleaned_data
        
class ChangeBookStatusForm(BaseBookInstanceForm):

    def clean(self) -> dict:
        cleaned_data = super().clean()

        status_data = self.cleaned_data.get('status')
        due_back_data = self.cleaned_data.get('due_back')

        if status_data == InstanceStatus.AVAILABLE:
            if due_back_data:
                self.add_error('due_back', _('Invalid due back value for this status'))

        return cleaned_data

