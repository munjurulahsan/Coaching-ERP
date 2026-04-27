from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.db.models import Sum, Max, Count
from datetime import date
from django.http import JsonResponse
from .models import Coach, Client, Session, Payment, Batch
from .forms import ClientForm, PaymentForm, BatchForm, ClientEditForm

def get_client_name(request):
    batch_id = request.GET.get('batch_id')
    roll = request.GET.get('roll')
    if batch_id and roll:
        try:
            client = Client.objects.get(batch_id=batch_id, roll=roll)
            return JsonResponse({'name': client.name})
        except Client.DoesNotExist:
            return JsonResponse({'name': ''})
    return JsonResponse({'name': ''})

def get_next_roll(request):
    batch_id = request.GET.get('batch_id')
    if batch_id:
        max_roll = Client.objects.filter(batch_id=batch_id).aggregate(max_roll=Max('roll'))['max_roll'] or 0
        next_roll = max_roll + 1
        return JsonResponse({'next_roll': next_roll})
    return JsonResponse({'next_roll': 1})

def home(request):
    today = date.today()
    start_of_month = today.replace(day=1)

    total_students = Client.objects.count()
    total_batches = Batch.objects.count()
    total_payments = Payment.objects.count()
    daily_total = Payment.objects.filter(date=today, status='paid').aggregate(total=Sum('amount'))['total'] or 0
    monthly_total = Payment.objects.filter(date__gte=start_of_month, status='paid').aggregate(total=Sum('amount'))['total'] or 0
    batches = Batch.objects.all()

    context = {
        'daily_total': daily_total,
        'monthly_total': monthly_total,
        'batches': batches,
        'total_students': total_students,
        'total_batches': total_batches,
        'total_payments': total_payments,
    }
    return render(request, 'coaching/home.html', context)

def add_student(request):
    client_form = ClientForm(request.POST or None)
    if request.method == 'POST' and client_form.is_valid():
        client = client_form.save(commit=False)
        # Auto-assign roll
        max_roll = Client.objects.filter(batch=client.batch).aggregate(max_roll=Max('roll'))['max_roll'] or 0
        client.roll = max_roll + 1
        client.save()
        return redirect('client_list')
    context = {
        'client_form': client_form,
    }
    return render(request, 'coaching/add_student.html', context)


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            updated_client = form.save(commit=False)
            if updated_client.batch != client.batch:
                max_roll = Client.objects.filter(batch=updated_client.batch).aggregate(max_roll=Max('roll'))['max_roll'] or 0
                updated_client.roll = max_roll + 1
            updated_client.save()
            return redirect('client_profile', pk=client.pk)
    else:
        form = ClientEditForm(instance=client, initial={'roll': client.roll})

    return render(request, 'coaching/client_edit.html', {'form': form, 'client': client})


def manage_payment(request):
    payment_form = PaymentForm(request.POST or None)
    if request.method == 'POST' and payment_form.is_valid():
        batch = payment_form.cleaned_data['batch']
        roll = payment_form.cleaned_data['roll']
        amount = payment_form.cleaned_data['amount']
        date_val = payment_form.cleaned_data['date']
        status = payment_form.cleaned_data['status']
        try:
            client = Client.objects.get(batch=batch, roll=roll)
            payment = Payment(client=client, amount=amount, date=date_val, status=status)
            payment.save()
            return redirect('payment_list')
        except Client.DoesNotExist:
            payment_form.add_error('roll', 'No student found with this roll in the selected batch.')
    payments = Payment.objects.all().order_by('-date')
    context = {
        'payment_form': payment_form,
        'payments': payments,
    }
    return render(request, 'coaching/manage_payment.html', context)


def batch_create(request):
    form = BatchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('batch_list')
    return render(request, 'coaching/batch_form.html', {
        'form': form,
        'title': 'Create New Batch',
        'submit_text': 'Create Batch',
    })


def batch_edit(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    form = BatchForm(request.POST or None, instance=batch)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('batch_list')
    return render(request, 'coaching/batch_form.html', {
        'form': form,
        'title': f'Edit Batch: {batch.name}',
        'submit_text': 'Update Batch',
    })

class CoachListView(ListView):
    model = Coach
    template_name = 'coaching/coach_list.html'

class ClientListView(ListView):
    model = Client
    template_name = 'coaching/client_list.html'

class SessionListView(ListView):
    model = Session
    template_name = 'coaching/session_list.html'

class PaymentListView(ListView):
    model = Payment
    template_name = 'coaching/payment_list.html'
    context_object_name = 'payments'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('payment_form', PaymentForm())
        return context

    def post(self, request, *args, **kwargs):
        form = PaymentForm(request.POST)
        if form.is_valid():
            batch = form.cleaned_data['batch']
            roll = form.cleaned_data['roll']
            amount = form.cleaned_data['amount']
            date_val = form.cleaned_data['date']
            status = form.cleaned_data['status']
            try:
                client = Client.objects.get(batch=batch, roll=roll)
                Payment.objects.create(client=client, amount=amount, date=date_val, status=status)
                return redirect('payment_list')
            except Client.DoesNotExist:
                form.add_error('roll', 'No student found with this roll in the selected batch.')
        self.object_list = self.get_queryset()
        context = self.get_context_data(payment_form=form)
        return self.render_to_response(context)


def client_profile(request, pk):
    client = get_object_or_404(Client, pk=pk)
    payments = Payment.objects.filter(client=client).order_by('-date')
    context = {
        'client': client,
        'payments': payments,
        'total_paid': client.paid_amount(),
        'payment_count': client.total_payments(),
    }
    return render(request, 'coaching/client_profile.html', context)


def batch_list(request):
    batches = Batch.objects.annotate(student_count=Count('client')).all()
    batch_info = []
    for batch in batches:
        paid_amount = Payment.objects.filter(client__batch=batch, status='paid').aggregate(total=Sum('amount'))['total'] or 0
        batch_info.append({
            'batch': batch,
            'student_count': batch.student_count(),
            'paid_amount': paid_amount,
            'paid_students': batch.unique_students_paid(),
        })
    return render(request, 'coaching/batch_list.html', {'batch_info': batch_info})


def payment_report(request):
    batches = Batch.objects.all()
    selected_batch_id = request.GET.get('batch')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    payments = Payment.objects.select_related('client', 'client__batch').all().order_by('-date')

    if selected_batch_id:
        payments = payments.filter(client__batch_id=selected_batch_id)
    if from_date:
        payments = payments.filter(date__gte=from_date)
    if to_date:
        payments = payments.filter(date__lte=to_date)

    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = payments.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'batches': batches,
        'payments': payments,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'selected_batch_id': int(selected_batch_id) if selected_batch_id else None,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'coaching/payment_report.html', context)


def payment_status_check(request):
    client_data = None
    payment_history = []
    error_message = None
    
    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        roll = request.POST.get('roll')
        
        if batch_id and roll:
            try:
                client_data = Client.objects.get(batch_id=batch_id, roll=roll)
                payment_history = Payment.objects.filter(client=client_data).order_by('-date')
            except Client.DoesNotExist:
                error_message = 'Student not found with this roll in the selected batch.'
        else:
            error_message = 'Please select both batch and enter roll number.'
    
    batches = Batch.objects.all()
    context = {
        'batches': batches,
        'client_data': client_data,
        'payment_history': payment_history,
        'error_message': error_message,
    }
    return render(request, 'coaching/payment_status_check.html', context)

def batch_wise_payment_summary(request):
    batches = Batch.objects.all()
    batch_summary = []
    
    for batch in batches:
        total_students = Client.objects.filter(batch=batch).count()
        paid_students = Payment.objects.filter(client__batch=batch, status='paid').values('client').distinct().count()
        pending_students = total_students - paid_students
        total_pending_amount = Payment.objects.filter(client__batch=batch, status='pending').aggregate(total=Sum('amount'))['total'] or 0
        
        batch_summary.append({
            'batch': batch,
            'total_students': total_students,
            'paid_students': paid_students,
            'pending_students': pending_students,
            'total_pending_amount': total_pending_amount,
        })
    
    context = {
        'batch_summary': batch_summary,
    }
    return render(request, 'coaching/batch_wise_payment_summary.html', context)
