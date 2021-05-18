import json
import os
import requests
import shutil

from tempfile import mkdtemp
from zipfile import ZipFile

CHUNK_SIZE = 128


def get_data_from_grid(url: str = None) -> dict:
    grid_downloaded_file = 'grid_data_dump.zip'
    grid_unzipped_folder = mkdtemp()
    response = requests.get(url=url, stream=True)
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
