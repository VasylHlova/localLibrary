import datetime


from  django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BookInstance

class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(help_text='Enter a date between now and 4 weeks (default 3).')

    def clean_renewal_date(self):
        data = self.cleaned_data.get('renewal_date')

        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))  
        
        return data
    
class BorrowOrReserveBookForm(forms.ModelForm):
        STATUS_CHOISES = (
                            ('o', 'Borrow'),
                            ('r', 'Reserve'),
                        )

        status = forms.ChoiceField(choices=STATUS_CHOISES, label='What do you wish?', widget=forms.RadioSelect)

        class Meta:
             model = BookInstance
             fields = ['due_back', 'status']

             widgets = {
                  'due_back': forms.DateInput(attrs={'placeholder': '1999-12-31'})
             }

        def clean_due_back(self):
            data = self.cleaned_data.get('due_back')

            if data < datetime.date.today():
                raise ValidationError(_('Invalid date - renewal in past'))

            if data > datetime.date.today() + datetime.timedelta(weeks=4):
                raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))  
            
            return data
        
class ChangeBookStatusForm(forms.ModelForm):
     
    class Meta:
         model = BookInstance
         fields = ['status', 'due_back']

    def clean_due_back(self):
            data = self.cleaned_data.get('due_back')
            
            if not data:
                 return data

            if data < datetime.date.today():
                raise ValidationError(_('Invalid date - renewal in past'))

            if data > datetime.date.today() + datetime.timedelta(weeks=4):
                raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))  
            
            return data

    def clean(self):
         super().clean()

         status_data = self.cleaned_data['status']
         due_back_data = self.cleaned_data['due_back']

         if status_data  == 'r' or status_data == 'o':
              if not due_back_data: 
                   raise ValidationError(_('Date must be defined'))
         if status_data == 'a':
              if due_back_data:
                   raise ValidationError(_('Invalid due back value for this status'))



