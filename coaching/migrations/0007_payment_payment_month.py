# Generated manually for selecting the salary month on payments.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0006_client_monthly_fee'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_month',
            field=models.CharField(blank=True, max_length=7),
        ),
    ]
