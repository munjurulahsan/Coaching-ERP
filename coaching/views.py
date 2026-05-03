from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Exists, OuterRef
from django.db import transaction
from datetime import date
import calendar
import re
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Coach, Client, Session, Payment, Batch
from .forms import ClientForm, PaymentForm, PaymentEditForm, BatchForm, ClientEditForm, BulkStudentImportForm
from .sms import notify_payment_received


def format_payment_month(payment):
    if payment.payment_month:
        try:
            year, month = payment.payment_month.split('-', 1)
            return f"{calendar.month_name[int(month)]} {year}"
        except (ValueError, IndexError):
            return payment.payment_month
    return payment.date.strftime('%B %Y')


def format_month_value(month_value):
    if not month_value:
        return ''
    try:
        year, month = month_value.split('-', 1)
        return f"{calendar.month_name[int(month)]} {year}"
    except (ValueError, IndexError):
        return month_value


def month_range(start_date, end_date):
    months = []
    year = start_date.year
    month = start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        month_value = f'{year}-{month:02d}'
        months.append({
            'raw_month': month_value,
            'month': format_month_value(month_value),
        })
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def get_client_admission_date(client):
    return client.admission_date


def get_monthly_due_months(client, until_date=None):
    if client.monthly_fee <= 0:
        return []

    until_date = until_date or date.today()
    admission_date = get_client_admission_date(client)
    paid_months = set(
        Payment.objects.filter(
            client=client,
            fee_type='monthly',
            status='paid',
        )
        .exclude(payment_month='')
        .values_list('payment_month', flat=True)
    )

    due_months = []
    for month in month_range(admission_date, until_date):
        raw_month = month['raw_month']
        if raw_month in paid_months:
            continue
        due_months.append({
            **month,
            'amount': str(client.monthly_fee),
        })
    return due_months


def get_last_cleared_month(client):
    payment = (
        Payment.objects.filter(
            client=client,
            fee_type='monthly',
            status='paid',
            amount__gt=0,
        )
        .exclude(payment_month='')
        .order_by('-payment_month', '-date', '-id')
        .first()
    )
    if not payment:
        payment = (
            Payment.objects.filter(
                client=client,
                fee_type='monthly',
                status='paid',
                amount__gt=0,
            )
            .order_by('-date', '-id')
            .first()
        )
    return payment


def find_duplicate_payment(client, fee_type, payment_month):
    if fee_type != 'monthly' or not payment_month:
        return None
    return (
        Payment.objects.filter(
            client=client,
            fee_type=fee_type,
            payment_month=payment_month,
        )
        .order_by('-date', '-id')
        .first()
    )


def add_duplicate_payment_error(form, client, fee_type, payment_month):
    duplicate_payment = find_duplicate_payment(client, fee_type, payment_month)
    if not duplicate_payment:
        return False
    form.add_error(
        'payment_month',
        (
            f'{client.name} already has a {duplicate_payment.get_fee_type_display()} '
            f'entry for {format_payment_month(duplicate_payment)}. Edit that payment instead.'
        ),
    )
    return True


def resolve_payment_client(batch, roll=None, name=''):
    students = Client.objects.filter(batch=batch)
    if roll:
        try:
            return students.get(roll=str(roll).strip()), None
        except Client.DoesNotExist:
            return None, 'No student found with this roll in the selected batch.'

    name = (name or '').strip()
    if not name:
        return None, 'Search by roll or student name before saving payment.'

    exact_matches = students.filter(name__iexact=name)
    if exact_matches.count() == 1:
        return exact_matches.first(), None

    matches = students.filter(name__icontains=name)
    if matches.count() == 1:
        return matches.first(), None
    if matches.count() > 1:
        return None, 'Multiple students matched this name. Please use roll number.'
    return None, 'No student found with this name in the selected batch.'


def get_next_roll_value(batch):
    start_roll = str(batch.start_roll or '1').strip()
    start_match = re.match(r'^(.*?)(\d+)$', start_roll)
    if not start_match:
        count = Client.objects.filter(batch=batch).count()
        return start_roll if count == 0 else f'{start_roll}-{count + 1}'

    prefix, start_number = start_match.groups()
    number_width = len(start_number)
    roll_numbers = [int(start_number) - 1]
    for roll in Client.objects.filter(batch=batch).values_list('roll', flat=True):
        roll_text = str(roll).strip()
        match = re.match(rf'^{re.escape(prefix)}(\d+)$', roll_text)
        if match:
            roll_numbers.append(int(match.group(1)))
    next_number = max(roll_numbers) + 1
    return f'{prefix}{str(next_number).zfill(number_width)}'


@login_required
def get_client_name(request):
    batch_id = request.GET.get('batch_id')
    roll = request.GET.get('roll')
    name = request.GET.get('name', '')
    payment_month = request.GET.get('payment_month', '')
    fee_type = request.GET.get('fee_type', 'monthly')
    if not batch_id:
        return JsonResponse({'name': '', 'monthly_fee': '', 'due_payments': []})

    try:
        batch = Batch.objects.get(pk=batch_id)
    except Batch.DoesNotExist:
        return JsonResponse({'name': '', 'monthly_fee': '', 'due_payments': []})

    if name.strip() and not roll:
        matches = Client.objects.filter(batch=batch, name__icontains=name.strip()).order_by('roll', 'name')[:20]
        match_count = matches.count()
        return JsonResponse({
            'name': '',
            'monthly_fee': '',
            'error': 'Select the correct roll for this student name.' if match_count else 'No student found with this name in the selected batch.',
            'matches': [
                {
                    'id': student.pk,
                    'name': student.name,
                    'roll': student.roll,
                    'phone': student.phone,
                }
                for student in matches
            ],
            'due_payments': [],
        })

    client, error = resolve_payment_client(batch, roll=roll, name=name)
    if not client:
        return JsonResponse({'name': '', 'monthly_fee': '', 'error': error, 'due_payments': []})

    due_payments = get_monthly_due_months(client)

    selected_month_paid = False
    selected_month_duplicate = None
    if payment_month:
        selected_month_duplicate = find_duplicate_payment(client, fee_type, payment_month)
        selected_month_paid = Payment.objects.filter(
            client=client,
            fee_type='monthly',
            payment_month=payment_month,
            status='paid',
            amount__gt=0,
        ).exists()

    is_paused_for_month = bool(
        payment_month
        and client.status == 'paused'
        and client.pause_month == payment_month
    )
    admission_fee_paid = Payment.objects.filter(
        client=client,
        fee_type='admission',
        status='paid',
        amount__gt=0,
    ).exists()
    admission_date = get_client_admission_date(client)
    last_cleared_payment = get_last_cleared_month(client)

    return JsonResponse({
        'id': client.pk,
        'name': client.name,
        'roll': client.roll,
        'monthly_fee': str(client.monthly_fee),
        'status': client.status,
        'admission_date': admission_date.isoformat() if admission_date else '',
        'admission_date_display': admission_date.strftime('%d %b %Y') if admission_date else '',
        'pause_month': client.pause_month,
        'status_comment': client.status_comment,
        'is_paused_for_month': is_paused_for_month,
        'selected_month_paid': selected_month_paid,
        'selected_month_duplicate': bool(selected_month_duplicate),
        'selected_month_duplicate_status': selected_month_duplicate.status.capitalize() if selected_month_duplicate else '',
        'selected_month_duplicate_amount': str(selected_month_duplicate.amount) if selected_month_duplicate else '',
        'last_cleared_month': format_payment_month(last_cleared_payment) if last_cleared_payment else '',
        'last_cleared_month_raw': last_cleared_payment.payment_month if last_cleared_payment else '',
        'last_cleared_amount': str(last_cleared_payment.amount) if last_cleared_payment else '',
        'last_cleared_date': last_cleared_payment.date.isoformat() if last_cleared_payment else '',
        'admission_fee_paid': admission_fee_paid,
        'due_payments': due_payments,
        'due_count': len(due_payments),
    })

@login_required
def get_next_roll(request):
    batch_id = request.GET.get('batch_id')
    if batch_id:
        batch = get_object_or_404(Batch, pk=batch_id)
        has_students = Client.objects.filter(batch=batch).exists()
        next_roll = get_next_roll_value(batch)
        return JsonResponse({'next_roll': next_roll, 'has_students': has_students})
    return JsonResponse({'next_roll': 1, 'has_students': False})

@login_required
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

@login_required
def add_student(request):
    client_form = ClientForm(request.POST or None)
    if request.method == 'POST' and client_form.is_valid():
        client = client_form.save(commit=False)
        has_students = Client.objects.filter(batch=client.batch).exists()
        manual_roll = (client_form.cleaned_data.get('roll') or '').strip()
        client.roll = get_next_roll_value(client.batch) if has_students else manual_roll or get_next_roll_value(client.batch)
        tuition_fee = client_form.cleaned_data.get('tuition_fee')
        client.save()
        admission_fee = client_form.cleaned_data.get('admission_fee')
        if admission_fee:
            payment = Payment.objects.create(client=client, fee_type='admission', amount=admission_fee, date=date.today(), status='paid')
            notify_payment_received(payment)
        if tuition_fee:
            payment = Payment.objects.create(
                client=client,
                fee_type='monthly',
                amount=tuition_fee,
                payment_month=date.today().strftime('%Y-%m'),
                date=date.today(),
                status='paid',
            )
            notify_payment_received(payment)
        return redirect('client_list')
    context = {
        'client_form': client_form,
    }
    return render(request, 'coaching/add_student.html', context)


def parse_student_line(line):
    line = line.strip()
    if not line:
        return None, None

    if ',' in line:
        name, phone = [part.strip() for part in line.split(',', 1)]
    elif '\t' in line:
        name, phone = [part.strip() for part in line.split('\t', 1)]
    else:
        parts = line.rsplit(maxsplit=1)
        if len(parts) != 2:
            return None, None
        name, phone = parts

    return name, phone


@login_required
def import_students(request):
    form = BulkStudentImportForm(request.POST or None)
    result = None

    if request.method == 'POST' and form.is_valid():
        batch = form.cleaned_data['batch']
        lines = form.cleaned_data['students'].splitlines()
        next_roll = get_next_roll_value(batch)
        created = []
        skipped = []
        existing_phones = set(Client.objects.values_list('phone', flat=True))

        with transaction.atomic():
            for line_number, line in enumerate(lines, start=1):
                name, phone = parse_student_line(line)
                if not name and not phone:
                    if line.strip():
                        skipped.append(f'Line {line_number}: could not read name and phone')
                    continue
                if name.lower() == 'name' and phone.lower() in {'phone', 'number', 'mobile'}:
                    continue
                if not name or not phone:
                    skipped.append(f'Line {line_number}: missing name or phone')
                    continue
                if phone in existing_phones:
                    skipped.append(f'Line {line_number}: {phone} already exists')
                    continue

                Client.objects.create(
                    name=name,
                    phone=phone,
                    email=None,
                    goals='',
                    batch=batch,
                    roll=next_roll,
                )
                created.append({'name': name, 'phone': phone, 'roll': next_roll})
                existing_phones.add(phone)
                next_roll = get_next_roll_value(batch)

        result = {
            'batch': batch,
            'created': created,
            'skipped': skipped,
        }

    return render(request, 'coaching/import_students.html', {
        'form': form,
        'result': result,
    })


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientEditForm(request.POST, instance=client)
        if form.is_valid():
            updated_client = form.save(commit=False)
            if updated_client.batch != client.batch:
                updated_client.roll = get_next_roll_value(updated_client.batch)
            updated_client.save()
            return redirect('client_profile', pk=client.pk)
    else:
        form = ClientEditForm(instance=client, initial={'roll': client.roll})

    return render(request, 'coaching/client_edit.html', {'form': form, 'client': client})


@login_required
@require_POST
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        redirect_url = next_url
    else:
        redirect_url = 'client_list'
    client.delete()
    return redirect(redirect_url)


@login_required
def manage_payment(request):
    return redirect('payment_list')


@login_required
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


@login_required
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


@login_required
@require_POST
def batch_delete(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    batch.delete()
    return redirect('batch_list')


class CoachListView(LoginRequiredMixin, ListView):
    model = Coach
    template_name = 'coaching/coach_list.html'

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'coaching/client_list.html'

    def get_queryset(self):
        batch_id = self.request.GET.get('batch')
        name = self.request.GET.get('name', '').strip()
        roll = self.request.GET.get('roll', '').strip()

        if not batch_id and not name and not roll:
            return Client.objects.none()

        students = Client.objects.select_related('batch')
        if batch_id:
            students = students.filter(batch_id=batch_id)
        if name:
            students = students.filter(name__icontains=name)
        if roll:
            students = students.filter(roll=roll)
        return students.order_by('batch__name', 'roll', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_batch_id = self.request.GET.get('batch') or ''
        name_query = self.request.GET.get('name', '').strip()
        roll_query = self.request.GET.get('roll', '').strip()
        context['batches'] = Batch.objects.all().order_by('name', 'time')
        context['selected_batch_id'] = selected_batch_id
        context['selected_batch'] = Batch.objects.filter(pk=selected_batch_id).first() if selected_batch_id else None
        context['name_query'] = name_query
        context['roll_query'] = roll_query
        context['has_filter'] = bool(selected_batch_id or name_query or roll_query)
        return context

class SessionListView(LoginRequiredMixin, ListView):
    model = Session
    template_name = 'coaching/session_list.html'

class PaymentListView(LoginRequiredMixin, ListView):
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
            name = form.cleaned_data['name']
            amount = form.cleaned_data['amount']
            payment_month = form.cleaned_data['payment_month']
            date_val = form.cleaned_data['date']
            fee_type = form.cleaned_data['fee_type']
            client, error = resolve_payment_client(batch, roll=roll, name=name)
            if client:
                if not add_duplicate_payment_error(form, client, fee_type, payment_month):
                    payment = Payment.objects.create(client=client, fee_type=fee_type, amount=amount, payment_month=payment_month, date=date_val, status='paid')
                    notify_payment_received(payment)
                    return redirect('payment_list')
            else:
                form.add_error('roll' if roll else 'name', error)
        self.object_list = self.get_queryset()
        context = self.get_context_data(payment_form=form)
        return self.render_to_response(context)


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('client', 'client__batch'), pk=pk)
    old_status = payment.status
    form = PaymentEditForm(request.POST or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        payment = form.save()
        if old_status != 'paid':
            notify_payment_received(payment)
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('payment_list')

    return render(request, 'coaching/payment_edit.html', {
        'form': form,
        'payment': payment,
        'next': request.GET.get('next', ''),
    })


@login_required
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


@login_required
def batch_list(request):
    batches = Batch.objects.annotate(total_students=Count('client')).all()
    batch_info = []
    for batch in batches:
        paid_students = batch.unique_students_paid()
        batch_info.append({
            'batch': batch,
            'student_count': batch.total_students,
            'paid_students': paid_students,
            'unpaid_students': max(batch.total_students - paid_students, 0),
        })
    return render(request, 'coaching/batch_list.html', {'batch_info': batch_info})


@login_required
def payment_report(request):
    today = date.today()
    batches = Batch.objects.all()
    selected_batch_id = request.GET.get('batch')
    selected_payment_month = request.GET.get('payment_month', '').strip()
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    payments = Payment.objects.select_related('client', 'client__batch').all().order_by('-date')
    collection_payments = Payment.objects.filter(status='paid')
    clients = Client.objects.select_related('batch').all()
    selected_batch = None
    batch_student_rows = []

    if selected_batch_id:
        payments = payments.filter(client__batch_id=selected_batch_id)
        collection_payments = collection_payments.filter(client__batch_id=selected_batch_id)
        clients = clients.filter(batch_id=selected_batch_id)
        selected_batch = Batch.objects.filter(pk=selected_batch_id).first()
    if from_date:
        payments = payments.filter(date__gte=from_date)
    if to_date:
        payments = payments.filter(date__lte=to_date)

    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = payments.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0
    daily_collection_payments = (
        collection_payments.select_related('client', 'client__batch')
        .filter(date=today)
        .order_by('client__batch__name', 'client__roll', 'client__name', 'id')
    )
    monthly_collection_payments = (
        collection_payments.select_related('client', 'client__batch')
        .filter(date__year=today.year, date__month=today.month)
        .order_by('-date', 'client__batch__name', 'client__roll', 'client__name', 'id')
    )
    for payment in daily_collection_payments:
        payment.display_month = format_payment_month(payment)
    for payment in monthly_collection_payments:
        payment.display_month = format_payment_month(payment)
    daily_collection = sum(payment.amount for payment in daily_collection_payments)
    monthly_collection = sum(payment.amount for payment in monthly_collection_payments)
    admission_payments = Payment.objects.filter(client=OuterRef('pk'), fee_type='admission')
    paid_admission_payments = admission_payments.filter(status='paid', amount__gt=0)
    if selected_batch:
        monthly_paid_payments = Payment.objects.select_related('client').filter(
            client__batch=selected_batch,
            fee_type='monthly',
            status='paid',
            amount__gt=0,
        ).order_by('-date', '-id')
        if selected_payment_month:
            monthly_paid_payments = monthly_paid_payments.filter(payment_month=selected_payment_month)
        elif from_date:
            monthly_paid_payments = monthly_paid_payments.filter(date__gte=from_date)
        if not selected_payment_month and to_date:
            monthly_paid_payments = monthly_paid_payments.filter(date__lte=to_date)

        monthly_payments_by_student = {}
        for payment in monthly_paid_payments:
            payment.display_month = format_payment_month(payment)
            monthly_payments_by_student.setdefault(payment.client_id, []).append(payment)

        due_students = clients
        if selected_payment_month:
            due_students = due_students.exclude(status='paused', pause_month=selected_payment_month)
        else:
            due_students = due_students.filter(status='active')

        batch_students = (
            due_students.annotate(
                has_paid_admission=Exists(paid_admission_payments),
            )
            .order_by('roll', 'name')
        )
        for student in batch_students:
            student_monthly_payments = monthly_payments_by_student.get(student.pk, [])
            paid_months = [payment.display_month for payment in student_monthly_payments]
            batch_student_rows.append({
                'student': student,
                'has_paid_monthly': bool(student_monthly_payments),
                'has_paid_admission': student.has_paid_admission,
                'monthly_payments': student_monthly_payments,
                'paid_months': ', '.join(paid_months),
            })

    total_batch_students = len(batch_student_rows)
    monthly_paid_count = sum(1 for row in batch_student_rows if row['has_paid_monthly'])
    monthly_due_count = total_batch_students - monthly_paid_count

    context = {
        'batches': batches,
        'payments': payments,
        'selected_batch': selected_batch,
        'batch_student_rows': batch_student_rows,
        'total_batch_students': total_batch_students,
        'monthly_paid_count': monthly_paid_count,
        'monthly_due_count': monthly_due_count,
        'daily_collection': daily_collection,
        'monthly_collection': monthly_collection,
        'daily_collection_payments': daily_collection_payments,
        'monthly_collection_payments': monthly_collection_payments,
        'collection_date': today,
        'collection_month_label': today.strftime('%B %Y'),
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'selected_batch_id': int(selected_batch_id) if selected_batch_id else None,
        'selected_payment_month': selected_payment_month,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'coaching/payment_report.html', context)


@login_required
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

@login_required
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
