# Generated manually for fixed monthly student fees.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0005_payment_fee_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='monthly_fee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
