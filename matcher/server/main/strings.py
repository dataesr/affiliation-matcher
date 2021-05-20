import collections
import string
import unicodedata

from typing import Dict


def remove_punction(s):
    for p in string.punctuation:
        s = s.replace(p, ' ').replace('  ', ' ')
    return s.strip()


def strip_accents(text: str) -> str:
    """Normalize accents and stuff in string."""
    text = text.replace('’', ' ')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def delete_punctuation(text: str) -> str:
    """Delete all punctuation in a string."""
    return text.lower().translate(str.maketrans(string.punctuation, len(string.punctuation) * ' '))


def generate_str_id_from_dict(dictionary: Dict, sort: bool = True) -> str:
    """Return a normalized stringify dict."""
    return normalize_text(stringify_dict(dictionary, sort=sort))


def stringify_dict(dictionary: Dict, sort: bool = True) -> str:
    """Stringify a dictionary."""
    text = ''
    if sort is True:
        for k, v in collections.OrderedDict(dictionary).items():
            text += str(v)
    else:
        for k, v in dictionary.items():
            text += str(v)
    return text


def normalize_text(text: str = None, remove_separator: bool = True) -> str:
    """Normalize string. Delete punctuation and accents."""
    if isinstance(text, str):
        text = text.replace('\xa0', ' ').replace('\n', ' ')
        text = delete_punctuation(text)
        text = strip_accents(text)
        sep = '' if remove_separator else ' '
        text = sep.join(text.split())
    return text or ''
