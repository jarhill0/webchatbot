from exchange_translation import default as default_func, exchange_type, keywords, prompt
from name_exchange import name_exchange
from queue_exchange import queue_exchange, queue_exchange_prompt
from session_interface import get_session, log, set_session
from send_sms import send_message
from tangent_exchange import tangent_exchange_prompt, tangent_exchange
from text_util import clean

EXCHANGE_TYPES_NEXT = {'name': name_exchange, 'queue': queue_exchange, 'tangent': tangent_exchange}
EXCHANGE_TYPES_PROMPT = {'queue': queue_exchange_prompt,
                         'tangent': tangent_exchange_prompt}  # for special fetching of prompts
EXCHANGE_TYPES_AUTOFOLLOW = {'tangent': True}


def process_chat(session, message):
    """Process a chat session based on the session and message.

    :param session: The unique session identifier.
    :param message: The user's message.
    :returns: The next message, if there is an appropriate one, otherwise None.
    """
    log(session=session, message=message, is_from_user=True)
    response = process_chat_real(session, message)
    if response is not None:
        response = autofollow(session, response)
    if response is not None:
        log(session=session, message=response, is_from_user=False)
    return response


def autofollow(session, response):
    """Autofollow, if necessary.

    :param session: The session involved.
    :param response: The response to proactively send if we are autofollowing.
    :returns: The final response
    """
    while need_autofollow(session):
        send_message(session, response)
        response = process_chat_real(session, '')
    return response


def need_autofollow(session):
    curr_exchange, _ = get_session(session)
    exch_type = exchange_type(curr_exchange)
    return EXCHANGE_TYPES_AUTOFOLLOW.get(exch_type, False)


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
    cleaned_words = clean(message).lower().split()
    if '?' in message:
        cleaned_words.append('question')
    for mess_word in cleaned_words:
        if mess_word in mapping:
            new_exchange = mapping[mess_word]
            break

    if new_exchange:
        set_session(session, new_exchange, data)
        return get_prompt(session, new_exchange, data)
    return None


def get_prompt(session, exchange, data):
    type_ = exchange_type(exchange)
    try:
        return EXCHANGE_TYPES_PROMPT[type_](session)
    except KeyError:
        return prompt(exchange, data)
