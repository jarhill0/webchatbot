from storage import TangentTracker, Tangents

TANGENTS = Tangents()
TRACKER = TangentTracker()


class NoTangentsException(Exception):
    """Raised when there are no tangents fitting a query."""


def all_tangents():
    """Iterate over all tangents.

    :returns: A 3-tuple of (id, rank, tangent).
    """
    return list(TANGENTS)


def delete_tangent(tangent_id):
    """Delete a particular tangent.

    :param tangent_id: The ID of the session to clear.
    """
    TANGENTS.delete(tangent_id)


def get_tangent(tangent_id):
    """Get a tangent.

    :param tangent_id: The ID of the tangent.
    :returns: A 3-tuple of (id, rank, tangent).
    """
    row = TANGENTS.get(tangent_id)
    if row is None:
        return None, None, None
    return row


def get_unseen_tangent(user_id):
    """Get a tangent the user hasn't seen and mark it as seen.

    :param user_id: The ID of a user.
    :returns: The text of the first tangent the user hasn't seen.
    """
    seen = set(thing[0] for thing in TRACKER.get_all_seen(user_id))
    print(seen)
    for tangent_id, _, text in all_tangents():
        if tangent_id not in seen:
            TRACKER.set_seen(tangent_id, user_id)
            return text
    raise NoTangentsException('No unseen tangents for user {!r}.'.format(user_id))


def set_tangent(rank, tangent_text, tangent_id=None):
    """Set a tangent.

    :param rank: The rank of the tangent.
    :param tangent_text: The text of the tangent.
    :param tangent_id: The id of a preexisting tangent to modify (default: None).
    """
    TANGENTS.set(rank, tangent_text, tangent_id)
