from django import forms
from datetime import date
from .models import Client, Payment, Batch


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
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))
    admission_fee = forms.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Admission fee', 'step': '0.01'}))

    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'batch']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'batch': forms.Select(attrs={'class': 'form-control', 'id': 'id_client_batch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_email(self):
        return self.cleaned_data.get('email') or None

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if Client.objects.filter(phone=phone).exists():
            raise forms.ValidationError('A student with this phone number already exists.')
        return phone

class PaymentForm(forms.Form):
    batch = forms.ModelChoiceField(queryset=Batch.objects.all(), widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_batch'}))
    roll = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by roll', 'id': 'id_roll'}))
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by student name', 'id': 'id_name'}))
    fee_type = forms.ChoiceField(choices=Payment.FEE_TYPE_CHOICES, initial='monthly', widget=forms.Select(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount (BDT)'}))
    payment_month = forms.CharField(
        required=False,
        label='Payment Month',
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
    )
    date = forms.DateField(label='Payment Date', initial=date.today, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    status = forms.ChoiceField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')], widget=forms.Select(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('roll') and not cleaned_data.get('name'):
            raise forms.ValidationError('Search by roll or student name before saving payment.')
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


class ClientEditForm(forms.ModelForm):
    roll = forms.CharField(required=False, disabled=True, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}))

    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'monthly_fee', 'batch', 'status', 'pause_month', 'status_comment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Student monthly fee', 'step': '0.01'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'pause_month': forms.TextInput(attrs={'class': 'form-control', 'type': 'month'}),
            'status_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Example: Student will not study next month'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monthly_fee'].required = False
        self.fields['pause_month'].required = False

    def clean_email(self):
        return self.cleaned_data.get('email') or None

    def clean_monthly_fee(self):
        return self.cleaned_data.get('monthly_fee') or 0

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
