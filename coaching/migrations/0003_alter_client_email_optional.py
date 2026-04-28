# Generated manually for optional student email support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0002_batch_client_roll_client_batch_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]
