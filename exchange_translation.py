from storage import Keywords, Prompts

KEYWORDS = Keywords()
PROMPTS = Prompts()


def all_exchanges():
    """Get the all Exchanges in the format (name, prompt, default)."""
    return iter(PROMPTS)


def default(exchange_name):
    """Get the default successor of an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    return PROMPTS.get_default(exchange_name)


def delete(exchange_name):
    """Delete an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    PROMPTS.delete(exchange_name)
    KEYWORDS.delete(exchange_name)


def keywords(exchange_name):
    """Get the keywords of an exchange.

    :param exchange_name: The name of the Exchange.
    """
    return KEYWORDS.get_mapping(exchange_name)


def prompt(exchange_name):
    """Get the prompt of an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    return PROMPTS.get_prompt(exchange_name)


def rank(exchange_name):
    """Get the rank of an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    return PROMPTS.get_rank(exchange_name)


def save_to_disk(exchange_name, prompt_, keyword_map, default_=None, rank_=None):
    """Save an Exchange to disk, updating existing entries if needed.

    :param exchange_name: The name of the Exchange.
    :param prompt_: The Exchange's prompt.
    :param keyword_map: A dict mapping keywords to Exchange names.
    :param default_: The default successor Exchange (default: None).
    :param rank_: The Exchange's rank.
    """
    PROMPTS.set(exchange_name, prompt_, default_, rank_)
    KEYWORDS.set_many(exchange_name, keyword_map)
