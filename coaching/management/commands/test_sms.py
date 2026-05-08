from django.core.management.base import BaseCommand, CommandError

from coaching.models import Payment
from coaching.sms import normalize_bd_sms_number, payment_sms_message, send_sms_detailed


class Command(BaseCommand):
    help = "Send a test SMS or resend the latest payment SMS for production troubleshooting."

    def add_arguments(self, parser):
        parser.add_argument("phone", nargs="?", help="Bangladesh mobile number, e.g. 017XXXXXXXX")
        parser.add_argument(
            "--message",
            default="Test SMS from Easy Chemistry For HSC",
            help="SMS text when sending to a direct phone number.",
        )
        parser.add_argument(
            "--latest-payment",
            action="store_true",
            help="Send the latest paid payment SMS to that student's guardian number.",
        )

    def handle(self, *args, **options):
        if options["latest_payment"]:
            payment = (
                Payment.objects
                .select_related("client")
                .filter(status="paid")
                .order_by("-date", "-id")
                .first()
            )
            if not payment:
                raise CommandError("No paid payment found.")
            phone = payment.client.guardian_phone
            message = payment_sms_message(payment)
            self.stdout.write(f"Latest payment: #{payment.pk} for {payment.client.name}")
        else:
            phone = options.get("phone")
            message = options["message"]
            if not phone:
                raise CommandError("Phone number is required unless --latest-payment is used.")

        normalized_phone = normalize_bd_sms_number(phone)
        self.stdout.write(f"Raw phone: {phone}")
        self.stdout.write(f"Normalized phone: {normalized_phone or 'INVALID'}")
        self.stdout.write(f"Message length: {len(message)}")
        self.stdout.write(f"Message: {message}")

        result = send_sms_detailed(phone, message)
        self.stdout.write(f"Gateway sent flag: {result['sent']}")
        self.stdout.write(f"Gateway phone: {result['phone_number']}")
        self.stdout.write(f"Gateway status: {result['status_code']}")
        self.stdout.write(f"Gateway response: {result['response']}")
