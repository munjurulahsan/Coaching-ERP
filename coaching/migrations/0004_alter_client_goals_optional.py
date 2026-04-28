# Generated manually for name-and-phone student imports.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0003_alter_client_email_optional'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='goals',
            field=models.TextField(blank=True),
        ),
    ]
