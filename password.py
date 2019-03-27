from getpass import getpass

from storage import Secrets

SECRETS = Secrets()


def main():
    inp = ''
    while inp not in ('v', 's'):
        inp = input('Would you like to [v]iew or [s]et the password? ').lower()[:1]
    if inp == 'v':
        view_password()
    elif inp == 's':
        set_password()


def view_password():
    try:
        print('The password is {!r}.'.format(SECRETS['password']))
    except KeyError:
        print('There is no password set.')


def set_password():
    while True:
        while True:
            p1 = getpass('Enter new password: ')
            if p1:
                break
            print('Password cannot be empty.')

        p2 = getpass('Enter it again: ')
        if p1 == p2:
            break
        print('Passwords do not match.')

    SECRETS['password'] = p1


if __name__ == '__main__':
    main()
