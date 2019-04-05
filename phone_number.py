from storage import Secrets

SECRETS = Secrets()


def main():
    inp = ''
    while inp not in ('v', 's'):
        inp = input('Would you like to [v]iew or [s]et the phone number? ').lower()[:1]
    if inp == 'v':
        view_phone_number()
    elif inp == 's':
        set_phone_number()


def view_phone_number():
    try:
        print('The phone number is {!r}.'.format(SECRETS['phone_number']))
    except KeyError:
        print('There is no phone number set.')


def set_phone_number():
    SECRETS['phone_number'] = input('Enter the phone number in format +15017122661: ')


if __name__ == '__main__':
    main()
