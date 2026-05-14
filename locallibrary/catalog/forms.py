from datetime import date

from utils.choices import InstanceStatus
from utils.validators import validate_future_date, validate_term_limit
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import BookInstance


class ChangeBookInstanceDueBackBaseForm(forms.ModelForm):
    due_back = forms.DateField(
        help_text="Enter a date between now and 4 weeks (default 3).",
        validators=[validate_future_date, validate_term_limit],
    )

    class Meta:
        model = BookInstance
        fields = ["due_back"]

    def __init__(self, *args, **kwargs):
        self.desired_statuses = kwargs.pop(
            'desired_statuses', 
            getattr(self, 'desired_statuses', [])
        )
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        cleaned_data = super().clean()

        if self.instance.pk:
            current_status = BookInstance.objects.filter(pk=self.instance.pk).values_list("status", flat=True).first()
            if current_status and current_status not in self.desired_statuses:
                raise ValidationError(_(f"This book has bad status({current_status}) for this action!"))

        return cleaned_data


class ChangeBookInstanceStatusDueBackBaseForm(forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = ["status", "due_back"]

    def clean_due_back(self) -> date:
        data = self.cleaned_data.get("due_back")
        if data:
            validate_future_date(data)

        return data

    def clean(self)-> dict:
        cleaned_data = super().clean()

        status_data = self.cleaned_data.get("status")
        due_back_data = self.cleaned_data.get("due_back")

        if status_data and due_back_data:
            if status_data in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
                try:
                    validate_term_limit(due_back_data, status=status_data)
                except ValidationError as e:
                    self.add_error("due_back", e)

        return cleaned_data


class RenewBookForm(ChangeBookInstanceDueBackBaseForm):
    desired_statuses = [InstanceStatus.RESERVED, InstanceStatus.ON_LOAN]


class BorrowReservedBookForm(ChangeBookInstanceDueBackBaseForm):
    desired_statuses = [InstanceStatus.RESERVED]


class BorrowOrReserveBookForm(ChangeBookInstanceStatusDueBackBaseForm):
    STATUS_CHOICES = (
        (InstanceStatus.ON_LOAN, "Borrow"),
        (InstanceStatus.RESERVED, "Reserve"),
    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, label="What do you wish?", widget=forms.RadioSelect)

    class Meta(ChangeBookInstanceStatusDueBackBaseForm.Meta):
        widgets = {
            "due_back": forms.DateInput(
                attrs={
                    "placeholder": "1999-12-31",
                }
            )
        }

    def clean(self) -> dict:
        cleaned_data = super().clean()

        if self.instance.pk:
            current_status = BookInstance.objects.values_list("status", flat=True).get(pk=self.instance.pk)
            if current_status and current_status != InstanceStatus.AVAILABLE:
                raise ValidationError(_("This book is not available!"))

        return cleaned_data



class ChangeBookStatusForm(ChangeBookInstanceStatusDueBackBaseForm):
    def clean(self) -> dict:
        cleaned_data = super().clean()

        status_data = self.cleaned_data.get("status")
        due_back_data = self.cleaned_data.get("due_back")

        if status_data == InstanceStatus.AVAILABLE:
            if due_back_data:
                self.add_error("due_back", _("The due back field must be empty for this status!"))

        return cleaned_data
