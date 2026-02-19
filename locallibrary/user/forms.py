from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile
from common.validators import validate_user_age

class CustomSignupForm(forms.Form):

    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    def signup(self, request:HttpRequest, user:CustomUser) -> None:
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

class UpdateUserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="First Name", max_length=150, required=False)
    last_name = forms.CharField(label="Last Name", max_length=150, required=False)

    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['date_of_birth'].validators.append(validate_user_age)

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            profile.save()
        
        return profile


