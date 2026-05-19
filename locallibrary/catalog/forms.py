from utils.choices import InstanceStatus
from utils.validators import validate_future_date, validate_term_limit
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.models import BookInstance


class ChangeBookInstanceDueBackBaseForm(forms.ModelForm):
    due_back = forms.DateField(
        help_text="Enter a date between now and 4 weeks (default 3).",
        validators=[validate_future_date],  
    )

    class Meta:
        model = BookInstance
        fields = ["due_back"]

    def get_status(self) -> str:
        raise NotImplementedError("Subclasses must implement get_status()")

    def clean(self) -> dict:
        cleaned_data = super().clean()
        due_back = cleaned_data.get("due_back")
        if due_back:
            try:
                validate_term_limit(due_back, status=self.get_status())
            except ValidationError as e:
                self.add_error("due_back", e)
        return cleaned_data


class BookInstanceStatusDueBackValidationMixin:
    def clean_due_back(self) -> dict:
        data = self.cleaned_data.get("due_back")
        if data:
            validate_future_date(data)
        return data

    def clean(self) -> dict:
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        due_back = cleaned_data.get("due_back")
        if status and due_back:
            if status in [InstanceStatus.ON_LOAN, InstanceStatus.RESERVED]:
                try:
                    validate_term_limit(due_back, status=status)
                except ValidationError as e:
                    self.add_error("due_back", e)
        return cleaned_data


class RenewBookForm(ChangeBookInstanceDueBackBaseForm):
    def get_status(self) -> str:
        if self.instance is None:
            raise ValidationError(_("Cannot renew due back date without an instance."))
        return self.instance.status


class BorrowReservedBookForm(ChangeBookInstanceDueBackBaseForm):
    def get_status(self) -> str:
        return InstanceStatus.ON_LOAN

class BorrowOrReserveBookForm(BookInstanceStatusDueBackValidationMixin, forms.Form):
    STATUS_CHOICES = (
        (InstanceStatus.ON_LOAN, "Borrow"),
        (InstanceStatus.RESERVED, "Reserve"),
    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect)
    due_back = forms.DateField(
        widget=forms.DateInput(attrs={"placeholder": "1999-12-31"})
    )


class ChangeBookStatusForm(BookInstanceStatusDueBackValidationMixin, forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = ["status", "due_back"]

    def clean(self) -> dict:
        cleaned_data = super().clean()

        status_data = self.cleaned_data.get("status")
        due_back_data = self.cleaned_data.get("due_back")

        if status_data == InstanceStatus.AVAILABLE:
            if due_back_data:
                self.add_error("due_back", _("The due back field must be empty for this status!"))

        return cleaned_data
