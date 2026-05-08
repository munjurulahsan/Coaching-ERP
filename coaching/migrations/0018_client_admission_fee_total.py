from django.db import migrations, models


def copy_existing_admission_payments(apps, schema_editor):
    Client = apps.get_model('coaching', 'Client')
    Payment = apps.get_model('coaching', 'Payment')
    for client in Client.objects.all():
        paid_total = (
            Payment.objects.filter(client=client, fee_type='admission', status='paid')
            .aggregate(total=models.Sum('amount'))['total']
            or 0
        )
        if paid_total:
            client.admission_fee_total = paid_total
            client.save(update_fields=['admission_fee_total'])


class Migration(migrations.Migration):

    dependencies = [
        ('coaching', '0017_batchnoticerecipient_gateway_response_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='admission_fee_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(copy_existing_admission_payments, migrations.RunPython.noop),
    ]
