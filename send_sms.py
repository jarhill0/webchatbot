from os import environ

from twilio.rest import Client

from storage import Secrets

account_sid = environ.get('TWILIO_ACCOUNT_SID')
auth_token = environ.get('TWILIO_ACCOUNT_AUTH')
if not (account_sid and auth_token):
    raise Exception('Could not access Twilio authentication.')
TWILIO = Client(account_sid, auth_token)

SECRETS = Secrets()
PHONE_NUM = SECRETS['phone_number']


def send_sms(number, text):
    """Send an SMS message using Twilio.

    :param number: The phone number of the recipient.
    :param text: The contents of the message.
    """
    return TWILIO.messages.create(body=text, from_=PHONE_NUM, to=number)
