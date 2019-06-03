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


def send_sms(number, text, images):
    """Send an SMS message using Twilio.

    :param number: The phone number of the recipient.
    :param text: The contents of the message.
    :param images: A list of image URLs.
    """
    return TWILIO.messages.create(body=text, media_url=images, from_=PHONE_NUM, to=number)
