import json
import logging
import calendar
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    phone_number = (phone_number or '').strip()
    message = (message or '').strip()
    if not phone_number or not message:
        return False

    # Ensure phone number is in international format for Bangladesh
    if phone_number.startswith('01') and len(phone_number) == 11:
        phone_number = '88' + phone_number
    elif phone_number.startswith('8801') and len(phone_number) == 13:
        pass  # already correct
    else:
        logger.warning('Invalid phone number format for SMS: %s', phone_number)
        return False

    if not settings.SMS_ENABLED:
        logger.info('SMS skipped because SMS_ENABLED is false.')
        return False

    if not settings.SMS_API_URL or not settings.SMS_API_KEY:
        logger.warning('SMS skipped because SMS_API_URL or SMS_API_KEY is missing.')
        return False

    payload = {
        settings.SMS_API_KEY_PARAM: settings.SMS_API_KEY,
        settings.SMS_TO_PARAM: phone_number,
        settings.SMS_MESSAGE_PARAM: message,
    }
    if settings.SMS_SENDER_ID:
        payload[settings.SMS_SENDER_PARAM] = settings.SMS_SENDER_ID

    encoded_payload = urlencode(payload).encode('utf-8')
    method = settings.SMS_METHOD.upper()

    try:
        if method == 'GET':
            separator = '&' if '?' in settings.SMS_API_URL else '?'
            request = Request(f'{settings.SMS_API_URL}{separator}{encoded_payload.decode("utf-8")}', method='GET')
        else:
            request = Request(settings.SMS_API_URL, data=encoded_payload, method='POST')
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        with urlopen(request, timeout=settings.SMS_TIMEOUT_SECONDS) as response:
            response_body = response.read().decode('utf-8', errors='replace')
            logger.info('SMS gateway response %s for %s: %s', response.status, phone_number, response_body)
            if not 200 <= response.status < 300:
                return False
            try:
                response_data = json.loads(response_body)
            except json.JSONDecodeError:
                return True
            return int(response_data.get('error', 0)) == 0
    except Exception:
        logger.exception('SMS sending failed for %s', phone_number)
        return False


def payment_sms_message(payment):
    fee_type = payment.get_fee_type_display()
    month_text = ''
    if payment.payment_month:
        try:
            year, month = payment.payment_month.split('-', 1)
            month_text = f' for {calendar.month_name[int(month)]} {year}'
        except (ValueError, IndexError):
            month_text = f' for {payment.payment_month}'
    return (
        f'Payment received for {payment.client.name}. '
        f'Type: {fee_type}{month_text}. '
        f'Amount: {payment.amount} BDT. Thank you.'
    )


def notify_payment_received(payment):
    if payment.status != 'paid':
        return False
    return send_sms(payment.client.guardian_phone, payment_sms_message(payment))
