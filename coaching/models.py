from django.db import models
from django.db.models import Sum

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
    goals = models.TextField(blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
