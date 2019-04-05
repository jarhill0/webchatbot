from json import dumps, load, loads
from os.path import dirname, join

from exchange_translation import keywords, prompt
from storage import Sessions
from text_util import clean

SESSIONS = Sessions()

with open(join(dirname(__file__), 'static', 'names.json')) as f:
    NAMES = {name.lower() for name in load(f)}


def name_exchange(session, message):
    name = get_name(message)
    curr_exchange, data = SESSIONS.get(session)
    if data is None:
        data = dict()
    else:
        data = loads(data)
    mapping = keywords(curr_exchange)

    if name:
        data['name'] = name
        next_exch = mapping['yes_name']
    else:
        next_exch = mapping['no_name']

    SESSIONS.set(session, next_exch, dumps(data))
    return prompt(next_exch, data)


def get_name(message):
    for word in clean(message).lower().split():
        if word in NAMES:
            return word.title()
    return None
