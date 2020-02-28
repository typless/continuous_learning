# Continuously learning AI
AI is a living thing. It learns and makes mistakes.
This guide will show you how to integrate continuous learning with __typless__ into the existing workflow of your customers.

## Why do you need continuously learning AI?
Business processes vary from one company to another, even from one department to another inside the same company.
For example, when you are on-boarding a new supplier, you need to add it into your ERP system.
You need to define how to pay, when to pay, contact person, etc.
With all these parameters, you will set the process of business for it.
Will, you set the same process for all suppliers? Probably not.
Some of the suppliers will send you invoices daily, some weekly, some monthly.
Some invoices are paid with a credit card, others with bank transfer, etc.
Will every company have the same process for the same supplier? Probably not.
Can it change once it's set? Of course!

So the question is: __How to integrate data extraction to fit those prerequisites?__

Firstly, you need a solution that will __learn directly from your system__.
You don't want to add new steps to existing process.

Secondly, you need __continuously learning AI__ .
You want it to __reflect changes__ in your system as __fast__ as possible

Lastly, you need a service that speaks your language. Your supplier A has an ID 1234 in your database.
It would be nice if AI would tell you: "It is an invoice from supplier 1234.".
It would eliminate OCR errors and at least one database query.

All of that can be achieved with __typless__ - the continuously learning AI for data extraction.

Let's take a look at the example.

## Prerequisites
To easily follow, we suggest that, before reading further, you do these following steps:
1. Register at [__typless__](https://developers.typless.com)
2. Log in
3. Click the _Settings_ tab in the side nav bar to get API key
4. Create a new document type named _example_:
    * Click on the __Documents__ tab in the side nav
    * Click on the __+New__ button
    * For the _name_ set "__example__"
    * For the _OCR language_ select "__English__"
    * Click on the __Next__ button
    * Leave fields as they are and click on the __Confirm__ button 
    
5. Get code of the example Django project from [__this__](https://github.com/typless/continuous_learning) Github repository.
    ```bash
    git clone https://github.com/typless/continuous_learning.git
    ```
    Set the API key:
    ```bash
    export API_KEY=YOUR_API_KEY_FROM_SETTINGS_TAB
    ```
    To install requirements:
    ```bash
    pip install -r requirements.txt
    ```
    To run the development server:
    ```bash
    python manage.py runserver
    ```
    To see the application, open [localhost:8000](http://localhost:8000).

## Expenses tracking
Let's say we, Awesome company Inc., track our expenses with a simple application which allows us to:

* see the list of our suppliers
* add a new supplier
* see the list of received invoices
* add a new received invoice
* see details of the selected received invoice
* confirm the received invoice

Although we are an Awesome company, we are still lazy.
So we've decided to automate our data entry from received invoices.
We want to keep our process the same, but we want to eliminate keystrokes.
So what to do?
We need a data extraction service. We've searched the web and decided to go with __typless__.
So how to integrate it to meet the needs mentioned above?

## Integrate into existing workflow
We don't want to change our existing process. Nonetheless, we don't want to mess our code too much.
Before we added data extraction, our code in views looked like this:
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
Nothing special.
When we added a newly received invoice file, we created a new ReceivedInvoice instance by calling ```form.save()```.
Then user was redirected to the details page to enter missing data and confirm the invoice.
Therefore we've decided to added __typless__ data extraction request after ```form.save()```.
Code now looks like this:

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
We've added a single API call in which we uploaded the invoice file and selected the document type.
(We've created a document type named __example__ following steps at the beginning of this guide.)
After the response is returned, the ReceivedInvoice instance is updated with extracted data.

## Test data extraction
If you haven't already run the development server:
```bash
    python manage.py runserver
```
and visit [localhost:8000](http://localhost:8000).

There are no suppliers yet. So add two of them:
* __CircleCI__ with __bank transfer__ as the payment method
* __ScaleGrid__ with a __credit card__ as the payment method

You will find example invoices in the folder named __examples__.
Click on __Received invoices__ link in the navigation bar.
Choose file __circleci1.pdf__ and click __Submit__.

After clicking Submit, you will land on the received invoice details page.

But hey, invoice data fields are still empty! Didn't we just add data extraction?
Of course, they are, __typless__ has never been learning from your data. Let's do it.

## Continuously learn AI
__typless__ needs to learn to extract data.
Similar to data extraction, we can add continuous learning into our process.
Before we added __typless__, code looked like this:
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
Instance was just updated with the data from the request.
As for data extraction, to continuously learn AI, we need a single REST API call.
We've decided to insert it after instance update.
Code now looks like this:
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
            # ###### Start typless learning######
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
            # ###### Finish typless ######
            context = {'invoice': invoice, 'form': ReceivedInvoiceForm(instance=invoice)}
        else:
            context = {'invoice': invoice, 'form': form}
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return render(request, 'expenses/received_invoice_details.html', context)
```

If we take a look we can see:
* we added single API call
* we used data from our instance which is saved in the database

## Confirm values and test extraction again
Now enter missing data into the form at received invoice details page and click on the __Confirm__ button.
Return to received invoices list by clicking on link __Received invoices__ in the navigation bar.
Choose file __circleci2.pdf__ and click on the __Submit__ button.

You should see that extracted data are __full__ and __correct__.
Why is that? Because __typless__ have learned from you.

You can try the same flow with scalegrid1.pdf and scalegrid2.pdf from example invoices.
You can even use your invoices.

## Conclusion
We have learned how to integrate __typless__, the continuous learning AI, into the existing workflow.

What we've achieved:
* workflow stays the same
* __typless__ is learning from values in our database
* We have eliminated manual data entry
* __typless__ has learned to return the ID of supplier for a direct database update

To do that you need to integrate the following steps:

* Request on data extraction endpoint when the user adds a new PDF invoice
    * Save extracted data
    * Save __object_id__ from the response
* Request on learning endpoint when the user confirms data
    * Use __object_id__ from data extraction
    
 That's all! Happy OCRing!