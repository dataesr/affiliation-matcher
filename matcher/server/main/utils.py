import json
import os
import shutil
import string
import unicodedata
from tempfile import mkdtemp
from zipfile import ZipFile
import requests
import re

from matcher.server.main.config import GRID_DUMP_URL

CHUNK_SIZE = 128

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def remove_ref_index(query):
    """Remove the first 2 digits of a string if any."""
    rgx = re.compile("^(\d){1,2}([A-Za-z])(.*)")
    return rgx.sub("\\2\\3", query).strip()


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

def get_alpha2_from_french(user_input):
    ref = {"France": "fr", "Mexique": "mx", "Etats-Unis": "us", "Sénégal":"sn", "Chili": "cl", "Inde": "in", "Corée du Sud": "kr",
"Singapour": "sg", "Canada": "ca", "Pays-Bas": "nl", "Autriche": "at", "Japon": "jp", "Brésil": "br", "Chine": "cn",
          "Argentine": "ar", "Russie": "ru", "Italie": "it", "Ethiopie": "et", "Israël": "il", "Afrique du Sud": "za"}
    return ref.get(user_input)

def download_grid_data() -> dict:
    grid_downloaded_file = 'grid_data_dump.zip'
    grid_unzipped_folder = mkdtemp()
    response = requests.get(url=GRID_DUMP_URL, stream=True)
    with open(grid_downloaded_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(grid_downloaded_file, 'r') as file:
        file.extractall(grid_unzipped_folder)
    with open(f'{grid_unzipped_folder}/grid.json', 'r') as file:
        data = json.load(file)
    os.remove(path=grid_downloaded_file)
    shutil.rmtree(path=grid_unzipped_folder)
    return data


def has_a_digit(text: str = '') -> bool:
    for char in text:
        if char.isdigit():
            return True
    return False


def get_common_words(objects: list, field: string, split: bool = True, threshold: int = 10) -> list:
    dictionary = {}
    for obj in objects:
        for text in obj.get(field, []):
            if split:
                words = normalize_text(text=text, remove_separator=False).split(' ')
            else:
                words = [normalize_text(text=text, remove_separator=False)]
            for word in words:
                if word not in dictionary:
                    dictionary[word] = 0
                dictionary[word] += 1
    result = []
    for entry in dictionary:
        if dictionary[entry] >= threshold:
            result.append(entry)
    return result
