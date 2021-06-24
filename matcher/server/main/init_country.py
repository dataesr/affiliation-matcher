import json
import os

import pycountry

from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic

ES_INDEX = 'country'
FILE_FR_CITIES_INSEE = 'fr_cities_insee.csv'
FILE_FR_UNIVERSITIES_MESRI = 'fr_universities_mesri.json'

logger = get_logger(__name__)


def get_cities_from_insee() -> dict:
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_FR_CITIES_INSEE), 'r') as file:
        insee_cities = [line.rstrip() for line in file]
    return {'insee_cities': insee_cities}


def get_universities_from_mesri() -> dict:
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_FR_UNIVERSITIES_MESRI), 'r') as file:
        data = json.load(file)
        mesri_universities = [university['fields']['uo_lib_officiel'] for university in data]
    return {'mesri_universities': mesri_universities}


def get_names_from_country(alpha_2: str = None) -> dict:
    country = pycountry.countries.get(alpha_2=alpha_2)
    all_names = []
    if hasattr(country, 'name'):
        all_names.append(country.name)
    if hasattr(country, 'official_name'):
        all_names.append(country.official_name)
    if hasattr(country, 'common_name'):
        all_names.append(country.common_name)
        name = country.common_name
    else:
        name = country.name
    return {'alpha_2': country.alpha_2, 'alpha_3': country.alpha_3, 'all_names': all_names, 'name': name}


def init_country(index: str = ES_INDEX) -> None:
    es = MyElastic()
    settings = {
        'analysis': {
            'filter': {
                'length_min_3_char': {
                    'type': 'length',
                    'min': 3
                }
            },
            'analyzer': {
                'analyzer_name': {
                    'tokenizer': 'icu_tokenizer',
                    'filter': ['length_min_3_char']
                }
            }
        }
    }
    mappings = {
        'properties': {
            'all_names': {
                'type': 'text',
                'analyzer': 'analyzer_name'
            }
        }
    }
    es.create_index(index=index, settings=settings, mappings=mappings)
    actions = []
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {'_index': index}
        # GENERAL NAMES
        names = get_names_from_country(alpha_2=country)
        body.update(names)
        if country == 'fr':
            # INSEE CITIES
            body.update(get_cities_from_insee())
            # MESRI UNIVERSITIES
            body.update(get_universities_from_mesri())
        actions.append(body)
    es.parallel_bulk(actions=actions)
