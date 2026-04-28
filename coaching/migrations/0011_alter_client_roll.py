from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0010_batch_start_roll'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='roll',
            field=models.CharField(max_length=30),
        ),
    ]
