from string import ascii_letters, digits

_VALID_CHARS = ascii_letters + digits + ' '


def clean(s):
    """Clean a string of everything other than ascii letters and digits."""
    return ''.join(l for l in s if l in _VALID_CHARS)
