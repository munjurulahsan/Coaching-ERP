import json
import logging
import calendar
from urllib.parse import parse_qsl, urlencode
from urllib.request import Request, urlopen

from django.conf import settings


logger = logging.getLogger(__name__)


def normalize_bd_sms_number(phone_number):
    phone_number = (phone_number or '').strip()
    if phone_number.startswith('+88'):
        phone_number = phone_number[3:]
    phone_number = phone_number.replace(' ', '').replace('-', '')

    if phone_number.startswith('01') and len(phone_number) == 11:
        return '88' + phone_number
    if phone_number.startswith('8801') and len(phone_number) == 13:
        return phone_number
    return ''


def sms_success_from_response(response_body):
    try:
        response_data = json.loads(response_body)
    except json.JSONDecodeError:
        return True
    if 'success' in response_data:
        return bool(response_data.get('success'))
    if 'error' in response_data:
        try:
            return int(response_data.get('error', 0)) == 0
        except (TypeError, ValueError):
            return False
    return True


def send_sms_detailed(phone_number, message):
    normalized_phone_number = normalize_bd_sms_number(phone_number)
    message = (message or '').strip()
    if not normalized_phone_number or not message:
        logger.warning('Invalid SMS input. Phone: %s, has message: %s', phone_number, bool(message))
        return {
            'sent': False,
            'phone_number': normalized_phone_number or (phone_number or '').strip(),
            'status_code': None,
            'response': 'Invalid phone number or empty message.',
        }

    if not settings.SMS_ENABLED:
        logger.info('SMS skipped because SMS_ENABLED is false.')
        return {
            'sent': False,
            'phone_number': normalized_phone_number,
            'status_code': None,
            'response': 'SMS_ENABLED is false.',
        }

    if not settings.SMS_API_URL or not settings.SMS_API_KEY:
        logger.warning('SMS skipped because SMS_API_URL or SMS_API_KEY is missing.')
        return {
            'sent': False,
            'phone_number': normalized_phone_number,
            'status_code': None,
            'response': 'SMS_API_URL or SMS_API_KEY is missing.',
        }

    payload = dict(parse_qsl(settings.SMS_EXTRA_PARAMS, keep_blank_values=True))
    payload.update({
        settings.SMS_API_KEY_PARAM: settings.SMS_API_KEY,
        settings.SMS_TO_PARAM: normalized_phone_number,
        settings.SMS_MESSAGE_PARAM: message,
    })
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
            logger.info('SMS gateway response %s for %s: %s', response.status, normalized_phone_number, response_body)
            sent = 200 <= response.status < 300 and sms_success_from_response(response_body)
            return {
                'sent': sent,
                'phone_number': normalized_phone_number,
                'status_code': response.status,
                'response': response_body,
            }
    except Exception as exc:
        logger.exception('SMS sending failed for %s', normalized_phone_number)
        return {
            'sent': False,
            'phone_number': normalized_phone_number,
            'status_code': None,
            'response': str(exc),
        }


def send_sms(phone_number, message):
    return send_sms_detailed(phone_number, message)['sent']


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
