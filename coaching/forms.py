from django import forms
from datetime import date
from .models import BatchNotice, Client, Payment, Batch


def clean_bd_mobile_number(number):
    number = (number or '').strip().replace(' ', '').replace('-', '')
    if not number:
        return ''
    if number.startswith('+88'):
        number = number[3:]
    if number.startswith('8801') and len(number) == 13 and number.isdigit():
        return number
    if number.startswith('01') and len(number) == 11 and number.isdigit():
        return number
    raise forms.ValidationError('Enter a valid Bangladesh mobile number, e.g. 017XXXXXXXX or 88017XXXXXXXX.')


class BulkStudentImportForm(forms.Form):
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    students = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 12,
            'placeholder': 'Rahim Uddin, 01700000000\nKarim Ahmed, 01800000000',
        }),
        help_text='One student per line: Name, Phone',
    )


class ClientForm(forms.ModelForm):
    roll = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll number', 'readonly': 'readonly', 'id': 'id_client_roll'}))
    admission_fee_paid = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2, label='Admission Fee Paid Now', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount paid now', 'step': '0.01'}))
    tuition_fee = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tuition fee for running month', 'step': '0.01'}))

    class Meta:
        model = Client
        fields = ['name', 'phone', 'guardian_phone', 'monthly_fee', 'admission_fee_total', 'batch']
        labels = {
            'phone': "Student's Number",
            'guardian_phone': 'Guardian Number',
            'monthly_fee': 'Monthly Fee',
            'admission_fee_total': 'Admission Fee Total',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter student name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter student's number"}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guardian number'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fixed monthly fee', 'step': '0.01'}),
            'admission_fee_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Required admission fee', 'step': '0.01'}),
            'batch': forms.Select(attrs={'class': 'form-control', 'id': 'id_client_batch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['guardian_phone'].required = True
        self.fields['monthly_fee'].required = True
        self.fields['admission_fee_total'].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if Client.objects.filter(phone=phone).exists():
            raise forms.ValidationError('A student with this phone number already exists.')
        return phone

    def clean_guardian_phone(self):
        return clean_bd_mobile_number(self.cleaned_data.get('guardian_phone'))

    def clean_monthly_fee(self):
        return self.cleaned_data.get('monthly_fee') or 0

    def clean_admission_fee_total(self):
        return self.cleaned_data.get('admission_fee_total') or 0

class PaymentForm(forms.Form):
    batch = forms.ModelChoiceField(queryset=Batch.objects.all(), widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_batch'}))
    roll = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by roll', 'id': 'id_roll'}))
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by student name', 'id': 'id_name'}))
    fee_type = forms.ChoiceField(choices=Payment.FEE_TYPE_CHOICES, initial='monthly', widget=forms.Select(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(label='Amount Per Month', max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter monthly amount (BDT)', 'step': '0.01'}))
    payment_month = forms.CharField(
        required=False,
        label='Starting Month',
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
    )
    months_to_pay = forms.IntegerField(
        label='How Many Months',
        initial=1,
        min_value=1,
        max_value=24,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '24', 'step': '1', 'id': 'id_months_to_pay'}),
    )
    date = forms.DateField(label='Payment Date', initial=date.today, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('roll') and not cleaned_data.get('name'):
            raise forms.ValidationError('Search by roll or student name before saving payment.')
        if cleaned_data.get('fee_type') == 'monthly' and not cleaned_data.get('payment_month'):
            self.add_error('payment_month', 'Select the first month for this monthly payment.')
        if cleaned_data.get('fee_type') != 'monthly':
            cleaned_data['months_to_pay'] = 1
        return cleaned_data


class PaymentEditForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['fee_type', 'amount', 'payment_month', 'date', 'status']
        widgets = {
            'fee_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount (BDT)', 'step': '0.01'}),
            'payment_month': forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'time', 'start_roll']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch name'}),
            'time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch schedule, e.g. 9:00 AM - 11:00 AM'}),
            'start_roll': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First roll, e.g. 1 or M-27101'}),
        }


class BatchNoticeForm(forms.ModelForm):
    class Meta:
        model = BatchNotice
        fields = ['batch', 'recipient_type', 'active_students_only', 'message']
        labels = {
            'recipient_type': 'Send To',
            'active_students_only': 'Active students only',
        }
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'recipient_type': forms.Select(attrs={'class': 'form-control'}),
            'active_students_only': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'maxlength': 1000,
                'placeholder': 'Write your notice message',
            }),
        }

    def clean_message(self):
        message = (self.cleaned_data.get('message') or '').strip()
        if not message:
            raise forms.ValidationError('Notice message cannot be empty.')
        return message


class ClientEditForm(forms.ModelForm):
    roll = forms.CharField(required=False, disabled=True, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))

    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'guardian_phone', 'monthly_fee', 'admission_fee_total', 'batch', 'status', 'pause_month', 'status_comment']
        labels = {
            'phone': "Student's Number",
            'guardian_phone': 'Guardian Number',
            'admission_fee_total': 'Admission Fee Total',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter student's number"}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guardian number'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Student monthly fee', 'step': '0.01'}),
            'admission_fee_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Required admission fee', 'step': '0.01'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'pause_month': forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
            'status_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Example: Student will not study next month'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monthly_fee'].required = False
        self.fields['admission_fee_total'].required = False
        self.fields['pause_month'].required = False

    def clean_email(self):
        return self.cleaned_data.get('email') or None

    def clean_monthly_fee(self):
        return self.cleaned_data.get('monthly_fee') or 0

    def clean_admission_fee_total(self):
        return self.cleaned_data.get('admission_fee_total') or 0

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if self.instance.pk and phone == self.instance.phone:
            return phone
        existing_students = Client.objects.filter(phone=phone)
        if self.instance.pk:
            existing_students = existing_students.exclude(pk=self.instance.pk)
        if existing_students.exists():
            raise forms.ValidationError('A student with this phone number already exists.')
        return phone

    def clean_guardian_phone(self):
        return clean_bd_mobile_number(self.cleaned_data.get('guardian_phone'))
