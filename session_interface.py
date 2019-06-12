from json import dumps, loads

from storage import ChatLog, Sessions, TangentTracker

SESSIONS = Sessions()
CHATLOG = ChatLog()
TANGENT_TRACKER = TangentTracker()


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
    TANGENT_TRACKER.clear_user(session_id)


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


def log(session, message, is_from_user):
    """Add a log entry.

    :param session: The session ID.
    :param message: The message contents as str.
    :param is_from_user: Whether or not the message is from the user, as a bool.
    """
    CHATLOG.log(session=session, message=message, is_from_user=is_from_user)


def all_logged_convos():
    """Yield all conversations that have been logged.

    :returns: An iterable with the IDs of all logged conversations.
    """
    return CHATLOG


def get_log(session):
    """Get the log of a particular session.

    :param session: The name of the session.
    :returns: An iterable of (message, is_from_user, timestamp).
    """
    return CHATLOG.get(session)


def has_conversed(session):
    """Determine whether a particular user has ever conversed with us before.

    :param session: The session identifier, likely a phone number.
    :returns: A ``bool`` representing whether this user has conversed.
    """
    for row in get_log(session):
        return True
    return False
