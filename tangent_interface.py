from storage import Tangents

TANGENTS = Tangents()


def all_tangents():
    """Iterate over all tangents.

    :returns: A 3-tuple of (id, rank, tangent).
    """
    return TANGENTS


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


def set_tangent(rank, tangent_text, tangent_id=None):
    """Set a tangent.

    :param rank: The rank of the tangent.
    :param tangent_text: The text of the tangent.
    :param tangent_id: The id of a preexisting tangent to modify (default: None).
    """
    TANGENTS.set(rank, tangent_text, tangent_id)
