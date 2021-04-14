"""String utils."""
import string
import unicodedata
import collections
from typing import Dict

def remove_punction(s):
    for p in string.punctuation:
        s=s.replace(p,' ').replace('  ',' ')
    return s.strip()

def strip_accents(w: str) -> str:
    """Normalize accents and stuff in string."""
    return "".join(
        c for c in unicodedata.normalize("NFD", w)
        if unicodedata.category(c) != "Mn")


def delete_punct(w: str) -> str:
    """Delete all puctuation in a string."""
    return w.lower().translate(
        str.maketrans(string.punctuation, len(string.punctuation)*" "))


def generate_str_id_from_dict(dct: Dict, sort: bool = True) -> str:
    """Return a normalized stringify dict."""
    return normalize_text(stringify_dict(dct, sort=sort))


def stringify_dict(dct: Dict, sort: bool = True) -> str:
    """Stringify a dictionnary."""
    text = ""
    if sort is True:
        for k, v in collections.OrderedDict(dct).items():
            text += str(v)
    else:
        for k, v in dct.items():
            text += str(v)
    return text


def normalize_text(text: str, remove_sep=True) -> str:
    """Normalize string. Delete puctuation and accents."""
    if isinstance(text, str):
        text = text.replace("\n", " ")
        text = delete_punct(text)
        text = strip_accents(text)
        if remove_sep:
            sep = ""
        else:
            sep = " "
        text = sep.join(text.split())
    return text or ""
