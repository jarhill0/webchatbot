from json import dumps, loads

from storage import Sessions

SESSIONS = Sessions()


def all_sessions():
    """Iterate over all sessions.

    :returns: a 2-tuple of (session_id, current_exchange, data) where data is guaranteed to be a dict.
    """
    for session_id, curr_exchange, data in SESSIONS:
        if data is None:
            data = {}
        else:
            data = loads(data)
        yield session_id, curr_exchange, data


def clear_session(session_id):
    """Clear a particular session.

    :param session_id: The ID of the session to clear.
    """
    SESSIONS.delete(session_id)


def get_session(session_id):
    """Get the state of a session.

    :param session_id: The ID of the session, possibly not yet in existence.
    :returns: a 2-tuple of (current_exchange, data) where data is guaranteed to be a dict.
    """
    curr_exchange, data = SESSIONS.get(session_id)
    if data is None:
        data = {}
    else:
        data = loads(data)
    return curr_exchange, data


def set_session(session_id, current_exchange, data):
    """Set the state of a session.

    :param session_id: The ID of the session, possibly not yet in existence.
    :param current_exchange: The current exchange of the session as a str.
    :param data: The data of the session, as a dict or None.
    """
    if data is None:
        data = '{}'
    else:
        data = dumps(data)

    SESSIONS.set(session_id, current_exchange, data)
