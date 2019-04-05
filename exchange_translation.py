from jinja2 import Template

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


def exchange_type(exchange_name):
    """Get the type of an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    return PROMPTS.get_type(exchange_name)


def keywords(exchange_name):
    """Get the keywords of an exchange.

    :param exchange_name: The name of the Exchange.
    """
    return KEYWORDS.get_mapping(exchange_name)


def prompt(exchange_name, data=None):
    """Get the prompt of an Exchange.

    :param exchange_name: The name of the Exchange.
    :param data: (optional) Data to render as parameters to jinja2.
    """
    prompt_text = PROMPTS.get_prompt(exchange_name)
    if data is not None:
        template = Template(prompt_text)
        return template.render(**data)
    return prompt_text


def rank(exchange_name):
    """Get the rank of an Exchange.

    :param exchange_name: The name of the Exchange.
    """
    return PROMPTS.get_rank(exchange_name)


def save_to_disk(exchange_name, prompt_, keyword_map, default_=None, rank_=None, type_=None):
    """Save an Exchange to disk, updating existing entries if needed.

    :param exchange_name: The name of the Exchange.
    :param prompt_: The Exchange's prompt.
    :param keyword_map: A dict mapping keywords to Exchange names.
    :param default_: The default successor Exchange (default: None).
    :param rank_: The Exchange's rank (default: None).
    :param type_: The Exchange's type (default: None).
    """
    PROMPTS.set(exchange_name, prompt_, default_, rank_, type_)
    KEYWORDS.set_many(exchange_name, keyword_map)
