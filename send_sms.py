from urllib.parse import urlparse

from twilio.rest import Client

from session_interface import log
from storage import Secrets

SECRETS = Secrets()

try:
    PHONE_NUM = SECRETS['phone_number']
    ACCOUNT_SID = SECRETS['account_sid']
    AUTH_TOKEN = SECRETS['auth_token']
except KeyError:
    raise Exception('Could not access Twilio authentication. Configure it with twilio_auth.py.')

TWILIO = Client(ACCOUNT_SID, AUTH_TOKEN)


JANKY_GLOBALS = dict()


def send_sms(number, text, images):
    """Send an SMS message using Twilio.

    :param number: The phone number of the recipient.
    :param text: The contents of the message.
    :param images: A list of image URLs.
    """
    return TWILIO.messages.create(body=text, media_url=images, from_=PHONE_NUM, to=number)


def send_message(session, message):
    if message is None:
        return
    log(session=session, message=message, is_from_user=False)
    if session.startswith('+'):
        p = urlparse(JANKY_GLOBALS['request_url'])
        absolute_base = '{}://{}'.format(p.scheme, p.netloc)
        send_sms(session, **JANKY_GLOBALS['convert_func'](message, absolute_base))
