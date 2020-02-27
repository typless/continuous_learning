from django import forms

from expenses.models import Supplier, ReceivedInvoice


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'


class ReceivedInvoiceForm(forms.ModelForm):
    class Meta:
        model = ReceivedInvoice
        exclude = ['file', 'typless_id']


class CreateReceivedInvoiceForm(forms.ModelForm):
    class Meta:
        model = ReceivedInvoice
        fields = ['file']
