from django.db import models
from django.db.models import Sum
from datetime import date

class Batch(models.Model):
    name = models.CharField(max_length=100)
    time = models.CharField(max_length=50)  # e.g., "9:00 AM - 11:00 AM"
    start_roll = models.CharField(max_length=30, default='1')

    def __str__(self):
        return f"{self.name} ({self.time})"

    def student_count(self):
        return self.client_set.count()

    def paid_amount(self):
        return self.client_set.aggregate(total=Sum('payment__amount'))['total'] or 0

    def unique_students_paid(self):
        return self.client_set.filter(payment__status='paid').distinct().count()

class Coach(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Client(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15)
    guardian_phone = models.CharField(max_length=15, blank=True)
    admission_date = models.DateField(default=date.today)
    goals = models.TextField(blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admission_fee_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    roll = models.CharField(max_length=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    pause_month = models.CharField(max_length=7, blank=True)
    status_comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('batch', 'roll')

    def __str__(self):
        try:
            batch_name = self.batch.name if self.batch else "No Batch"
        except:
            batch_name = "No Batch"
        roll_str = f"Roll {self.roll}" if self.roll else "No Roll"
        return f"{self.name} ({roll_str}, {batch_name})"

    def paid_amount(self):
        return self.payment_set.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0

    def admission_paid_amount(self):
        return self.payment_set.filter(fee_type='admission', status='paid').aggregate(total=Sum('amount'))['total'] or 0

    def admission_due_amount(self):
        due_amount = self.admission_fee_total - self.admission_paid_amount()
        return due_amount if due_amount > 0 else 0

    def admission_fee_is_paid(self):
        if self.admission_fee_total <= 0:
            return self.admission_paid_amount() > 0
        return self.admission_due_amount() <= 0

    def total_payments(self):
        return self.payment_set.count()

    def due_amount(self):
        # if you want a fixed fee per student, update this logic accordingly
        return 0

class Session(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Session with {self.client.name} on {self.date}"

class Payment(models.Model):
    FEE_TYPE_CHOICES = [
        ('admission', 'Admission Fee'),
        ('monthly', 'Monthly Fee'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES, default='monthly')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_month = models.CharField(max_length=7, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ])

    def __str__(self):
        return f"{self.get_fee_type_display()} of {self.amount} by {self.client.name}"


class BatchNotice(models.Model):
    RECIPIENT_CHOICES = [
        ('guardian', 'Guardian numbers'),
        ('student', 'Student numbers'),
        ('both', 'Student and guardian numbers'),
    ]

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    message = models.TextField()
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, default='guardian')
    active_students_only = models.BooleanField(default=True)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notice to {self.batch.name} on {self.created_at:%Y-%m-%d %H:%M}"


class BatchNoticeRecipient(models.Model):
    notice = models.ForeignKey(BatchNotice, related_name='recipients', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    recipient_label = models.CharField(max_length=20)
    sent = models.BooleanField(default=False)
    gateway_status_code = models.PositiveIntegerField(blank=True, null=True)
    gateway_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['client__roll', 'client__name', 'recipient_label']

    def __str__(self):
        status = 'Sent' if self.sent else 'Failed'
        return f"{status}: {self.client.name} ({self.phone_number})"
