from string import digits, ascii_letters

from storage import Keywords, Prompts, Sessions

KEYWORDS = Keywords()
PROMPTS = Prompts()
SESSIONS = Sessions()
_VALID_CHARS = ascii_letters + digits + ' '


def process_chat(session, message):
    """Process a chat session based on the session and message.

    :param session: The unique session identifier.
    :param message: The user's message.
    :returns: The next message, if there is an appropriate one, otherwise None.
    """
    curr_exchange, data = SESSIONS.get(session)
    if curr_exchange is None:
        curr_exchange = 'start'

    mapping = KEYWORDS.get_mapping(curr_exchange)
    for mess_word in clean(message).lower().split():
        if mess_word in mapping:
            new_exchange = mapping[mess_word]
            SESSIONS.set(session, new_exchange, data)
            return PROMPTS.get_prompt(new_exchange)

    # default case
    default = PROMPTS.get_default(curr_exchange)
    if default:
        SESSIONS.set(session, default, data)
        return PROMPTS.get_prompt(default)
    else:
        return None


def clean(s):
    """Clean a string of everything other than ascii letters and digits."""
    return ''.join(l for l in s if l in _VALID_CHARS)
