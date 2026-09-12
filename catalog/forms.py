from django import forms

from cms.forms import HoneypotMixin

from .models import QuoteRequest, Service


class QuoteRequestForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = QuoteRequest
        fields = ["service", "name", "company", "email", "phone", "quantity", "details", "attachment"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "company": forms.TextInput(attrs={"placeholder": "Optional"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+974 5XXX XXXX", "autocomplete": "tel"}),
            "quantity": forms.TextInput(attrs={"placeholder": "e.g. 500 pages, 3 stamps"}),
            "details": forms.Textarea(
                attrs={"rows": 6, "placeholder": "Describe what you need: paper size, colour/B&W, binding type, deadline..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True)
        self.fields["service"].required = False
        self.fields["service"].empty_label = "General enquiry / other"
        self.fields["attachment"].help_text = "Optional: artwork or document (PDF, JPG, PNG, AI, EPS, SVG, DOCX, max 5 MB)."
