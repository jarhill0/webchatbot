from session_interface import get_session, set_session


def queue_exchange(session_id, message):
    return None  # do nothing, still queued.


def queue_exchange_prompt(session_id):
    mark_queued(session_id, True)
    return None  # no prompt


def mark_queued(session_id, status):
    exchange, data = get_session(session_id)
    data['queued'] = status
    set_session(session_id, exchange, data)
