from django import forms
from .models import Client, Payment, Batch

class ClientForm(forms.ModelForm):
    roll = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Roll number', 'readonly': 'readonly', 'id': 'id_client_roll'}))
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'goals', 'batch']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter goals'}),
            'batch': forms.Select(attrs={'class': 'form-control', 'id': 'id_client_batch'}),
        }

class PaymentForm(forms.Form):
    batch = forms.ModelChoiceField(queryset=Batch.objects.all(), widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_batch'}))
    roll = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter roll number', 'id': 'id_roll'}))
    name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student name', 'readonly': 'readonly', 'id': 'id_name'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount (BDT)'}))
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    status = forms.ChoiceField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')], widget=forms.Select(attrs={'class': 'form-control'}))


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['name', 'time']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch name'}),
            'time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch schedule, e.g. 9:00 AM - 11:00 AM'}),
        }


class ClientEditForm(forms.ModelForm):
    roll = forms.IntegerField(required=False, disabled=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}))

    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'goals', 'batch']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter goals'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
        }