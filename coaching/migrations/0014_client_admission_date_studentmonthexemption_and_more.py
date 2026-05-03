# Generated manually for admission dates and skipped payment months.

from datetime import date
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0013_client_guardian_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='admission_date',
            field=models.DateField(default=date.today),
        ),
        migrations.CreateModel(
            name='StudentMonthExemption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(max_length=7)),
                ('reason', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='month_exemptions', to='coaching.client')),
            ],
            options={
                'ordering': ['-month'],
                'unique_together': {('client', 'month')},
            },
        ),
        migrations.AlterField(
            model_name='client',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='coaching.batch'),
        ),
    ]
