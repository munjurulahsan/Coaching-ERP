# Generated manually after removing the skipped-month feature.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0014_client_admission_date_studentmonthexemption_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='StudentMonthExemption',
        ),
    ]
