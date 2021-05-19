import json
import os
import requests
import shutil

from tempfile import mkdtemp
from zipfile import ZipFile

from matcher.server.main.config import GRID_DUMP_URL
from matcher.server.main.strings import normalize_text

CHUNK_SIZE = 128


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
    os.remove(grid_downloaded_file)
    shutil.rmtree(grid_unzipped_folder)
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
