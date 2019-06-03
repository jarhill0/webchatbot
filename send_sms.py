from os import environ

from twilio.rest import Client

from storage import Secrets

SECRETS = Secrets()

try:
    PHONE_NUM = SECRETS['phone_number']
    ACCOUNT_SID = SECRETS['account_sid']
    AUTH_TOKEN = SECRETS['auth_token']
except KeyError:
    raise Exception('Could not access Twilio authentication. Configure it with twilio_auth.py.')

TWILIO = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_sms(number, text):
    """Send an SMS message using Twilio.

    :param number: The phone number of the recipient.
    :param text: The contents of the message.
    """
    return TWILIO.messages.create(body=text, from_=PHONE_NUM, to=number)
