from getpass import getpass

from storage import Secrets

SECRETS = Secrets()


def main():
    inp = ''
    while inp not in ('v', 's'):
        inp = input('Would you like to [v]iew or [s]et the Twilio authentication? ').lower()[:1]
    if inp == 'v':
        view_auth()
    elif inp == 's':
        set_auth()


def view_auth():
    for human_name, key_name in (('phone number', 'phone_number'), ('Twilio account SID', 'account_sid'),
                                 ('Twilio auth token', 'auth_token')):
        try:
            print('The {} is {!r}.'.format(human_name, SECRETS[key_name]))
        except KeyError:
            print('There is no {} set.'.format(human_name))


def set_auth():
    SECRETS['phone_number'] = input('Enter phone number: ')
    SECRETS['account_sid'] = input('Enter Twilio account SID: ')
    SECRETS['auth_token'] = getpass('Enter Twilio auth token: ')


if __name__ == '__main__':
    main()
