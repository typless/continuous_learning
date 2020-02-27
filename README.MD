# WIP: Continuous learning of typless AI
AI is a living thing. It learns and makes mistakes. This guide will show you how to integrate continuous learning with typless AI without any overhead for you or your customers.

## Prerequisites
To easily follow you should:
1. Register at [__typless__](https://developers.typless.com)
2. Login to [__typless__](https://developers.typless.com)
3. Get API key in _Settings_ tab from [__typless__](https://developers.typless.com)
4. Create new document type named example:
    * Click on _Documents_ tab in side nav
    * Click _+New_ button
    * For _name_ set __example__, for _OCR language_ select __English__
    * Click _Next_
    * Leave fields as it is and click _Confirm_ 
    
5. You can clone code of example Django project from [__this__](https://github.com/typless/continuous_learning) Github repository.
    ```bash
    git clone https://github.com/typless/continuous_learning.git
    ```
    
    To install requirements:
    ```bash
    pip install -r requirements.txt
    ```
    To run development server:
    ```bash
    python manage.py runserver
    ```
    To see application, open [localhost:8000](http://localhost:8000).
## Why do you need continuous learning?
Business processes vary from one company to another, even from one department to another inside the same company.
When you are on boarding a new supplier you need to add it into your ERP system.
You need to define how to pay, when to pay, contact person, etc. So it is a process.
Will you set the same process for all suppliers? Probably no.
What you need is an AI that will rapidly adapt to changes in your system - you need __typless__ continuous learning.

## Keep workflow the same
Lets say we, Awesome company Inc., track our expenses with simple application which allows us to:

* see list of our suppliers
* add new supplier
* see list of received invoices
* add new received invoice
* see details of selected received invoice
* confirmed received invoice

Although we are Awesome company, we are still lazy. So we decided to automate our data entry from received invoices.
We want to keep our process the same, we just want to eliminate key strokes. So what to to?
To do that, we need some kind of data extraction service - here comes __typless__. So how to integrate it to meet our needs?

## Integrate into existing workflow
If we want to ingerate like this we need to only add typless, without changing existing code.
Before we added typless, our views looked like this:
```python
# expenses/views.py
# ... other code ...
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
            # ##### End data extraction with typless ######

            return redirect(f'/received-invoices/{invoice.id}')
        else:
            received_invoices = models.ReceivedInvoice.objects.all()
            context = {'received_invoices': received_invoices, 'form': form}
            return render(request, 'expenses/received_invoices.html', context)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
        
 # ... other code

```
Nothing special. When we added new received invoice file, we created new ReceivedInvoice instance by calling ```form.save()```.
Then user was redirected to details page to enter missing data and confirm invoice. Therefore we added typless integration for data extraction after: ```form.save()```.
Code will now look like this: 

```python
# expenses/views.py
# ... other code ...
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
        
 # ... other code

```
We added call to typless endpoint for data extraction. After response is returned, we update ReceivedInvoice instance with extracted data.

## Test extraction
If you haven't already, run the development server:
```bash
    python manage.py runserver
```
and visit [localhost:8000](http://localhost:8000).

There are no suppliers yet. So add two of them:
* __CircleCI__ with __Bank transfer__ as payment method
* __ScaleGrid__ with __Credit Card__ as payment method

You will find example invoices in folder __examples__.
Click on __Received invoices__ link in navbar. Add one of example invoices with form and click __Submit__.

After clicking Submit, you will land on received invoice details page.

But hey, when you try it invoice data are still empty!
Of course they are, we did not learn typless yet.

## Use continuous learning
So we need to learn typless. Now here we come to the nice part. Similar as we added data extraction, we can add continuous learning into our process. Before we added typless code looked like this:
```python
# expenses/views.py
# ... other code ...
def received_invoice_details(request, pk):

    if request.method == 'GET':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
    elif request.method == 'POST':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        form = ReceivedInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save()
            # ###### Learn typless ######
            # ###### Finish learning typless ######
            context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
        else:
            context = {'invoice': invoice, 'form': form}
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'expenses/received_invoice_details.html', context)

```
Instance was just updated with data from request. To learn typless we need to add request to typless REST API with confirmed data.
```python
# expenses/views.py
# ... other code ...
def received_invoice_details(request, pk):

    if request.method == 'GET':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
    elif request.method == 'POST':
        invoice = models.ReceivedInvoice.objects.get(id=pk)
        form = ReceivedInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save()
            # ###### Learn typless ######
            if invoice.confirmed:
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
                requests.post(
                    "https://developers.typless.com/api/document-types/learn/",
                    data=request_data,
                    files={"document_object_id": (None, invoice.typless_id)},
                    headers={'Authorization': f'Token {os.getenv("API_KEY")}'}
                )
            # ###### Finish learning typless ######
            context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
        else:
            context = {'invoice': invoice, 'form': form}
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'expenses/received_invoice_details.html', context)

```

Now, after we update our ReceivedInvoice instance, we learn typless with confirmed values.

## Confirm values and test extraction again
Now enter missing data into form at received invoice details page and click __Confirm__.
Return to received invoices list by clicking on navbar link __Received invoices__. Now add another invoice from the same supplier as in previous step.

You should see that extracted data are __full__ and __correct__.

You can try the same flow with second supplier from example invoices.

## To sum up
We have learned how to integrate typless into exsiting workflow with continuous learning.

To do that you need to integrate following steps:

* Request on data extraction endpoint when user adds new PDF invoice
    * Save extracted data
    * Save __object_id__ from response
* Request on learning endpoint when user confirms data
    * Use __object_id__ from data extraction
    
 That's all! Happy OCRing!