from exchange_translation import default as default_func, exchange_type, keywords, prompt
from name_exchange import name_exchange
from queue_exchange import queue_exchange, queue_exchange_prompt
from session_interface import get_session, log, set_session
from text_util import clean

EXCHANGE_TYPES_NEXT = {'name': name_exchange, 'queue': queue_exchange}
EXCHANGE_TYPES_PROMPT = {'queue': queue_exchange_prompt}  # for special fetching of prompts


def process_chat(session, message):
    """Process a chat session based on the session and message.

    :param session: The unique session identifier.
    :param message: The user's message.
    :returns: The next message, if there is an appropriate one, otherwise None.
    """
    log(session=session, message=message, is_from_user=True)
    response = process_chat_real(session, message)
    if response is not None:
        log(session=session, message=response, is_from_user=False)
    return response


def process_chat_real(session, message):
    curr_exchange, data = get_session(session)  # guarantees data to be a dict
    if curr_exchange is None:
        curr_exchange = 'start'
        set_session(session, 'start', data)

    exch_type = exchange_type(curr_exchange)
    try:
        return EXCHANGE_TYPES_NEXT[exch_type](session, message)
    except KeyError:
        pass

    mapping = keywords(curr_exchange)
    new_exchange = default_func(curr_exchange)
    for mess_word in clean(message).lower().split():
        if mess_word in mapping:
            new_exchange = mapping[mess_word]
            break

    if new_exchange:
        set_session(session, new_exchange, data)
        new_exch_type = exchange_type(new_exchange)
        try:
            return EXCHANGE_TYPES_PROMPT[new_exch_type](session)
        except KeyError:
            return prompt(new_exchange, data)
    return None
