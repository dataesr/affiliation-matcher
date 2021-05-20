import json
import os
import requests
import shutil
import string
import unicodedata

from tempfile import mkdtemp
from zipfile import ZipFile

from matcher.server.main.config import GRID_DUMP_URL

CHUNK_SIZE = 128


def strip_accents(text: str) -> str:
    """Normalize accents and stuff in string."""
    text = text.replace('’', ' ')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def delete_punctuation(text: str) -> str:
    """Delete all punctuation in a string."""
    return text.lower().translate(str.maketrans(string.punctuation, len(string.punctuation) * ' '))


def normalize_text(text: str = None, remove_separator: bool = True) -> str:
    """Normalize string. Delete punctuation and accents."""
    if isinstance(text, str):
        text = text.replace('\xa0', ' ').replace('\n', ' ')
        text = delete_punctuation(text)
        text = strip_accents(text)
        sep = '' if remove_separator else ' '
        text = sep.join(text.split())
    return text or ''


def download_data_from_grid() -> dict:
    grid_downloaded_file = 'grid_data_dump.zip'
    grid_unzipped_folder = mkdtemp()
    response = requests.get(url=GRID_DUMP_URL, stream=True)
    with open(grid_downloaded_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(grid_downloaded_file, 'r') as file:
        file.extractall(grid_unzipped_folder)
    with open('{folder}/grid.json'.format(folder=grid_unzipped_folder), 'r') as file:
        data = json.load(file)
    os.remove(path=grid_downloaded_file)
    shutil.rmtree(path=grid_unzipped_folder)
    return data


def has_a_digit(x) -> bool:
    for c in x:
        if c.isdigit():
            return True
    return False


def get_common_words(x, field, split=True, threshold=10) -> list:
    common = {}
    for elt in x:
        for c in elt.get(field, []):
            if split:
                v = normalize_text(text=c, remove_separator=False).split(' ')
            else:
                v = [normalize_text(text=c, remove_separator=False)]
            for w in v:
                if w not in common:
                    common[w] = 0
                common[w] += 1
    result = []
    for w in common:
        if common[w] > threshold:
            result.append(w)
    return result
