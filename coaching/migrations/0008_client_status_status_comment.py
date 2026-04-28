# Generated manually for pausing students from monthly due reports.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0007_payment_payment_month'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('paused', 'Paused')],
                default='active',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='client',
            name='status_comment',
            field=models.TextField(blank=True),
        ),
    ]
