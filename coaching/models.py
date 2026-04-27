from django.db import models

class Batch(models.Model):
    name = models.CharField(max_length=100)
    time = models.CharField(max_length=50)  # e.g., "9:00 AM - 11:00 AM"

    def __str__(self):
        return f"{self.name} ({self.time})"

class Coach(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    goals = models.TextField()
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    roll = models.IntegerField()

    class Meta:
        unique_together = ('batch', 'roll')

    def __str__(self):
        try:
            batch_name = self.batch.name if self.batch else "No Batch"
        except:
            batch_name = "No Batch"
        roll_str = f"Roll {self.roll}" if self.roll else "No Roll"
        return f"{self.name} ({roll_str}, {batch_name})"

class Session(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Session with {self.client.name} on {self.date}"

class Payment(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ])

    def __str__(self):
        return f"Payment of {self.amount} by {self.client.name}"
