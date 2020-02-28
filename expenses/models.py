from django.db import models
from django.utils import timezone


class Supplier(models.Model):
    CREDIT_CARD = 'CREDIT_CARD'
    BANK_TRANSFER = 'BANK_TRANSFER'

    PAYMENT_METHODS = (
        (CREDIT_CARD, 'Credit card'),
        (BANK_TRANSFER, 'Bank transfer')
    )
    name = models.CharField('Name of our supplier', max_length=120)
    payment_method = models.CharField('How we will pay our supplier?', max_length=35, choices=PAYMENT_METHODS)

    def __str__(self):
        return f'{self.name}'


class ReceivedInvoice(models.Model):
    file = models.FileField('Invoice PDF file')
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,  # do not allow supplier delete if any invoice exists
        related_name='received_invoices',
        null=True
    )
    invoice_number = models.CharField('Invoice number', max_length=80, null=True, blank=True)
    issue_date = models.DateField('Issue date (YYYY-MM-DD)', default=timezone.now, null=True, blank=True)
    total_amount = models.DecimalField(decimal_places=2, max_digits=8, null=True)
    typless_id = models.CharField(max_length=32, null=True)

    def __str__(self):
        return f'{self.supplier} | {self.invoice_number} | {self.issue_date}'
