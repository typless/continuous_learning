import datetime
import os
import requests
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from expenses import models
from expenses.forms import SupplierForm, ReceivedInvoiceForm, CreateReceivedInvoiceForm


def suppliers_view(request):
    if request.method == 'GET':
        suppliers = models.Supplier.objects.all()
        context = {'suppliers': suppliers, 'form': SupplierForm()}

    elif request.method == 'POST':
        form = SupplierForm(data=request.POST)
        suppliers = models.Supplier.objects.all()

        if form.is_valid():
            form.save()
            form = SupplierForm()

        context = {'suppliers': suppliers, 'form': form}
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'expenses/suppliers.html', context)


def received_invoices_view(request):
    if request.method == 'GET':
        received_invoices = models.ReceivedInvoice.objects.all()
        context = {'received_invoices': received_invoices, 'form': CreateReceivedInvoiceForm()}
        return render(request, 'expenses/received_invoices.html', context)

    elif request.method == 'POST':
        form = CreateReceivedInvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save()
            # ###### Do data extraction with typless ######
            files = {

                "file": (invoice.file.name, invoice.file.read(),),
            }
            request_data = {
                "document_type_name": 'example',
                "customer": 'test'
            }
            if os.getenv("API_KEY") is None:
                raise Exception('YOU MUST SET API KEY TO ENVIRONMENT!')
            response = requests.post(
                f'https://developers.typless.com/api/document-types/extract-data/',
                files=files,
                data=request_data,
                headers={'Authorization': f'Token {os.getenv("API_KEY")}'}
            )

            fields = response.json()['extracted_fields']
            supplier = [field for field in fields if field['name'] == 'supplier'][0]['values'][0]['value']
            invoice_number = [field for field in fields if field['name'] == 'invoice_number'][0]['values'][0]['value']
            issue_date = [field for field in fields if field['name'] == 'issue_date'][0]['values'][0]['value']
            total_amount = [field for field in fields if field['name'] == 'total_amount'][0]['values'][0]['value']

            invoice.typless_id = response.json()['object_id']
            invoice.supplier_id = int(supplier) if supplier is not None else supplier
            invoice.invoice_number = invoice_number
            invoice.issue_date = datetime.datetime.strptime(issue_date, '%Y-%m-%d') if issue_date is not None else None
            invoice.total_amount = float(total_amount) if total_amount is not None else None
            invoice.save()
            # ##### End data extraction with typless ######

            return redirect(f'/received-invoices/{invoice.id}')
        else:
            received_invoices = models.ReceivedInvoice.objects.all()
            context = {'received_invoices': received_invoices, 'form': form}
            return render(request, 'expenses/received_invoices.html', context)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def received_invoice_details(request, pk):

    if request.method == 'GET':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
    elif request.method == 'POST':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        form = ReceivedInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save()
            # ###### Start typless learning######
            request_data = {
                "document_type_name": 'example',
                "customer": 'myself',
                "learning_fields": [
                    '{"name": "supplier", "value": "%s"}' %invoice.supplier.id,
                    '{"name": "invoice_number", "value": "%s"}' % invoice.invoice_number,
                    '{"name": "issue_date", "value": "%s"}' % invoice.issue_date.strftime('%Y-%m-%d'),
                    '{"name": "total_amount", "value": "%.2f"}' % invoice.total_amount
                ],
            }
            if os.getenv("API_KEY") is None:
                raise Exception('YOU MUST SET API KEY TO ENVIRONMENT!')
            requests.post(
                "https://developers.typless.com/api/document-types/learn/",
                data=request_data,
                files={"document_object_id": (None, invoice.typless_id)},
                headers={'Authorization': f'Token {os.getenv("API_KEY")}'}
            )
            # ###### Finish typless ######
            context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
        else:
            context = {'invoice': invoice, 'form': form}
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'expenses/received_invoice_details.html', context)