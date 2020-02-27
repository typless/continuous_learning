from django.contrib import admin


# Register your models here.
from expenses.models import Supplier, ReceivedInvoice


class SupplierAdmin(admin.ModelAdmin):
    pass


class ReceivedInvoiceAdmin(admin.ModelAdmin):
    pass


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(ReceivedInvoice, ReceivedInvoiceAdmin)
