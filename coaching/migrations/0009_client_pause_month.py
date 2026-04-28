# Generated manually for month-specific student pauses.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0008_client_status_status_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='pause_month',
            field=models.CharField(blank=True, max_length=7),
        ),
    ]
