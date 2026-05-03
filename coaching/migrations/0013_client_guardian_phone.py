# Generated manually for student guardian contact numbers.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0012_alter_batch_start_roll'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='guardian_phone',
            field=models.CharField(blank=True, max_length=15),
        ),
    ]
