from getpass import getpass

from storage import Secrets

SECRETS = Secrets()


def main():
    inp = ''
    while inp not in ('v', 's'):
        inp = input('Would you like to [v]iew or [s]et the welcome configuration? ').lower()[:1]
    if inp == 'v':
        view_welc()
    elif inp == 's':
        set_welc()


def view_welc():
    for human_name, key_name in (('welcome url', 'welcome_url'),
                                 ('welcome exchange name', 'welcome_exchange_name'),
                                 ('welcome system password', 'welcome_system_password'),):
        try:
            print('The {} is {!r}.'.format(human_name, SECRETS[key_name]))
        except KeyError:
            print('There is no {} set.'.format(human_name))


def set_welc():
    SECRETS['welcome_url'] = input('Enter URL of welcome chatbot: ')
    SECRETS['welcome_exchange_name'] = input('Enter welcome exchange name: ')
    SECRETS['welcome_system_password'] = getpass('Enter welcome system password: ')


if __name__ == '__main__':
    main()
