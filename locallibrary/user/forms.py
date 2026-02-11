from django import forms
from django.http import HttpRequest

from .models import CustomUser

class CustomSignupForm(forms.Form):

    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    def signup(self, request:HttpRequest, user:CustomUser) -> None:
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
