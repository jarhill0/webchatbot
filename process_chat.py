from exchange_translation import default as default_func, exchange_type, keywords, prompt
from name_exchange import name_exchange
from session_interface import get_session, set_session
from text_util import clean

EXCHANGE_TYPES = {'name': name_exchange}


def process_chat(session, message):
    """Process a chat session based on the session and message.

    :param session: The unique session identifier.
    :param message: The user's message.
    :returns: The next message, if there is an appropriate one, otherwise None.
    """
    curr_exchange, data = get_session(session)  # guarantees data to be a dict
    if curr_exchange is None:
        curr_exchange = 'start'

    exch_type = exchange_type(curr_exchange)
    try:
        return EXCHANGE_TYPES[exch_type](session, message)
    except KeyError:
        pass

    mapping = keywords(curr_exchange)
    for mess_word in clean(message).lower().split():
        if mess_word in mapping:
            new_exchange = mapping[mess_word]
            set_session(session, new_exchange, data)
            return prompt(new_exchange, data)

    # default case
    default = default_func(curr_exchange)
    if default:
        set_session(session, default, data)
        return prompt(default, data)
    else:
        return None
