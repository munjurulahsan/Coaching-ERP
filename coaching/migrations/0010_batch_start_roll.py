from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0009_client_pause_month'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='start_roll',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
