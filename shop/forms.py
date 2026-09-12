import re

from django import forms

from cms.forms import HoneypotMixin

from .models import Order

QATAR_PHONE_RE = re.compile(r"^(\+?974)?\s?[3-7]\d{3}\s?\d{4}$")


def normalise_phone(value: str) -> str:
    digits = re.sub(r"[^\d+]", "", value)
    if digits.startswith("+974"):
        return digits
    if digits.startswith("974"):
        return "+" + digits
    if len(digits) == 8:
        return "+974" + digits
    return digits


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1)
    custom_text = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Line 1\nLine 2\nLine 3"}),
        label="Stamp text / customisation",
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if product is not None and product.is_customisable:
            self.fields["custom_text"].required = True
            self.fields["custom_text"].help_text = product.customisation_help


class CheckoutForm(HoneypotMixin, forms.ModelForm):
    accepted_terms = forms.BooleanField(
        label="I have read and agree to the Terms & Conditions, Privacy Policy and Returns Policy.",
        error_messages={"required": "You must accept the terms to place an order."},
    )
    create_account = forms.BooleanField(required=False, label="Create an account to track my orders")

    class Meta:
        model = Order
        fields = [
            "full_name", "email", "phone", "company",
            "delivery_method", "building", "zone", "street", "area", "city", "delivery_notes",
            "payment_method", "accepted_terms",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+974 5XXX XXXX", "autocomplete": "tel"}),
            "company": forms.TextInput(attrs={"placeholder": "Optional"}),
            "delivery_method": forms.RadioSelect,
            "payment_method": forms.RadioSelect,
            "building": forms.TextInput(attrs={"placeholder": "Building no. / villa / office"}),
            "zone": forms.TextInput(attrs={"placeholder": "e.g. 56"}),
            "street": forms.TextInput(attrs={"placeholder": "e.g. 340"}),
            "area": forms.TextInput(attrs={"placeholder": "e.g. Salwa Road, Al Sadd"}),
            "delivery_notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Landmark, preferred delivery time..."}),
        }

    def __init__(self, *args, site=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = site
        choices = []
        if site is None or site.enable_cash_on_delivery:
            choices.append((Order.PaymentMethod.COD, Order.PaymentMethod.COD.label))
        if site is None or site.enable_card_on_delivery:
            choices.append((Order.PaymentMethod.CARD_ON_DELIVERY, Order.PaymentMethod.CARD_ON_DELIVERY.label))
        if site is None or site.enable_bank_transfer:
            choices.append((Order.PaymentMethod.BANK_TRANSFER, Order.PaymentMethod.BANK_TRANSFER.label))
        self.fields["payment_method"].choices = choices
        self.fields["delivery_method"].choices = Order.DeliveryMethod.choices

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not QATAR_PHONE_RE.match(phone.replace(" ", "")):
            raise forms.ValidationError("Enter a valid Qatar phone number (8 digits, optionally prefixed with +974).")
        return normalise_phone(phone)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("delivery_method") == Order.DeliveryMethod.DELIVERY:
            for field in ("building", "zone", "street", "area"):
                if not cleaned.get(field):
                    self.add_error(field, "Required for delivery.")
        return cleaned


class OrderTrackForm(forms.Form):
    number = forms.CharField(label="Order number", max_length=20, widget=forms.TextInput(attrs={"placeholder": "VA2026-00001"}))
    phone = forms.CharField(label="Phone number used at checkout", max_length=30, widget=forms.TextInput(attrs={"placeholder": "+974 5XXX XXXX"}))

    def clean_phone(self):
        return normalise_phone(self.cleaned_data["phone"])

    def clean_number(self):
        return self.cleaned_data["number"].strip().upper()
