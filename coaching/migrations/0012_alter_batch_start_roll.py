from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0011_alter_client_roll'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='start_roll',
            field=models.CharField(default='1', max_length=30),
        ),
    ]
