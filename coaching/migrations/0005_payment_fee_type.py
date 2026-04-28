# Generated manually for admission and monthly fee separation.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0004_alter_client_goals_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='fee_type',
            field=models.CharField(
                choices=[
                    ('admission', 'Admission Fee'),
                    ('monthly', 'Monthly Fee'),
                ],
                default='monthly',
                max_length=20,
            ),
        ),
    ]
