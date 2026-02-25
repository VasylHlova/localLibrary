from  django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BookInstance
from common.validators import validate_future_date, validate_term_limit
from common.choices import InstanceStatus

from datetime import date

class RenewBookForm(forms.ModelForm):
    due_back = forms.DateField(help_text='Enter a date between now and 4 weeks (default 3).',
                                   validators=[validate_future_date, validate_term_limit])
    class Meta:
        model = BookInstance
        fields = ['due_back']
    
class BaseBookInstanceForm(forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = ['status', 'due_back']

    def clean_due_back(self) -> date:
        data = self.cleaned_data.get('due_back')
        if data:
            validate_future_date(data)

        return data

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
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        cleaned_data = super().clean()

        if self.instance.pk:
            current_status = BookInstance.objects.values_list('status', flat=True).get(pk=self.instance.pk)
            if current_status and current_status != InstanceStatus.AVAILABLE:
                raise ValidationError(_('This book is not available!'))
                            
        return cleaned_data
    
    def save(self, commit: bool = True) -> BookInstance:
        instance =  super().save(commit=False)

        due_back = self.cleaned_data.get('due_back')
        status = self.cleaned_data.get('status')

        if commit:

            instance.borrow_book(self.user, due_back, status)
        
        return instance

class ChangeBookStatusForm(BaseBookInstanceForm):

    def clean(self) -> dict:
        cleaned_data = super().clean()

        status_data = self.cleaned_data.get('status')
        due_back_data = self.cleaned_data.get('due_back')

        if status_data == InstanceStatus.AVAILABLE:
            if due_back_data:
                self.add_error('due_back', _('The due back field must be empty for this status!'))

        return cleaned_data
    

    


