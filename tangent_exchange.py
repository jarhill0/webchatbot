import process_chat
from exchange_translation import default as default_func
from queue_exchange import mark_queued
from session_interface import get_session, set_session
from tangent_interface import NoTangentsException, get_unseen_tangent


def tangent_exchange(session_id, message):
    """Determine whether we're queued or not."""
    curr_exchange, data = get_session(session_id)
    if data.get('queued', False):
        return None  # stay right where we are
    new_exchange = default_func(curr_exchange)
    if new_exchange is None:
        return None
    set_session(session_id, new_exchange, data)
    return process_chat.get_prompt(session_id, new_exchange, data)


def tangent_exchange_prompt(session_id):
    try:
        return get_unseen_tangent(session_id)
    except NoTangentsException:
        mark_queued(session_id, True)
        return None
