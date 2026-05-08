from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from .models import Batch, Client, Payment


@override_settings(ALLOWED_HOSTS=['testserver'], FORCE_SCRIPT_NAME=None)
class PaymentListViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='staff', password='pass12345')
        self.batch = Batch.objects.create(name='HSC 26', time='9 AM', start_roll='1')
        self.client_obj = Client.objects.create(
            name='Rahim',
            phone='01700000000',
            guardian_phone='01800000000',
            admission_date=date(2026, 1, 1),
            monthly_fee=Decimal('1500.00'),
            batch=self.batch,
            roll='1',
        )
        self.client.login(username='staff', password='pass12345')

    @patch('coaching.views.notify_payment_received')
    def test_monthly_payment_can_cover_multiple_months(self, notify_payment_received):
        response = self.client.post('/payments/', {
            'batch': self.batch.pk,
            'roll': '1',
            'name': '',
            'fee_type': 'monthly',
            'amount': '1500.00',
            'payment_month': '2026-03',
            'months_to_pay': '3',
            'date': '2026-03-10',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Payment.objects.count(), 3)
        self.assertEqual(
            list(Payment.objects.order_by('payment_month').values_list('payment_month', flat=True)),
            ['2026-03', '2026-04', '2026-05'],
        )
        self.assertEqual(notify_payment_received.call_count, 3)

    @patch('coaching.views.notify_payment_received')
    def test_multi_month_payment_rejects_any_duplicate_month(self, notify_payment_received):
        Payment.objects.create(
            client=self.client_obj,
            fee_type='monthly',
            amount=Decimal('1500.00'),
            payment_month='2026-04',
            date=date(2026, 4, 5),
            status='paid',
        )

        response = self.client.post('/payments/', {
            'batch': self.batch.pk,
            'roll': '1',
            'name': '',
            'fee_type': 'monthly',
            'amount': '1500.00',
            'payment_month': '2026-03',
            'months_to_pay': '3',
            'date': '2026-03-10',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertContains(response, 'already has monthly payment entries for April 2026')
        notify_payment_received.assert_not_called()

    @patch('coaching.views.notify_payment_received')
    def test_add_student_tracks_partial_admission_fee_due(self, notify_payment_received):
        response = self.client.post('/add_student/', {
            'batch': self.batch.pk,
            'roll': '',
            'name': 'Karim',
            'phone': '01711111111',
            'guardian_phone': '01811111111',
            'monthly_fee': '1500.00',
            'admission_fee_total': '1500.00',
            'admission_fee_paid': '1000.00',
            'tuition_fee': '',
        })

        self.assertEqual(response.status_code, 302)
        student = Client.objects.get(name='Karim')
        self.assertEqual(student.admission_fee_total, Decimal('1500.00'))
        self.assertEqual(student.admission_paid_amount(), Decimal('1000.00'))
        self.assertEqual(student.admission_due_amount(), Decimal('500.00'))
        self.assertFalse(student.admission_fee_is_paid())
        notify_payment_received.assert_called_once()

    @patch('coaching.views.notify_payment_received')
    def test_add_student_accepts_discounted_admission_fee_as_paid(self, notify_payment_received):
        response = self.client.post('/add_student/', {
            'batch': self.batch.pk,
            'roll': '',
            'name': 'Nila',
            'phone': '01722222222',
            'guardian_phone': '01822222222',
            'monthly_fee': '1500.00',
            'admission_fee_total': '1000.00',
            'admission_fee_paid': '1000.00',
            'tuition_fee': '',
        })

        self.assertEqual(response.status_code, 302)
        student = Client.objects.get(name='Nila')
        self.assertEqual(student.admission_due_amount(), Decimal('0'))
        self.assertTrue(student.admission_fee_is_paid())
        notify_payment_received.assert_called_once()

    def test_payment_can_be_deleted(self):
        payment = Payment.objects.create(
            client=self.client_obj,
            fee_type='admission',
            amount=Decimal('1000.00'),
            date=date(2026, 4, 5),
            status='paid',
        )

        response = self.client.post(f'/payments/{payment.pk}/delete/', {'next': '/payments/'})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.filter(pk=payment.pk).exists())
