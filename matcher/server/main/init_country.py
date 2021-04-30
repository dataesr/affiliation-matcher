import json
import os
import pycountry

from elasticsearch import Elasticsearch
from matcher.server.main.config import config

ES_INDEX = 'country'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'
FILE_COUNTRY_WHITE_LIST = 'country_white_list.json'
FILE_FRENCH_CITIES = 'fr_cities.json'
FILE_FRENCH_UNIVERSITIES = 'fr_universities.json'


def get_info_from_country(alpha_2: str = None) -> dict:
    country = pycountry.countries.get(alpha_2=alpha_2)
    info = []
    if hasattr(country, 'name'):
        info.append(country.name)
    if hasattr(country, 'official_name'):
        info.append(country.official_name)
    if hasattr(country, 'common_name'):
        info.append(country.common_name)
    return {'alpha_2': country.alpha_2, 'alpha_3': country.alpha_3,
            'info': info}


def get_cities_from_country(alpha_2: str = None) -> dict:
    if alpha_2 == 'fr':
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, FILE_FRENCH_CITIES), 'r') as file:
            cities = json.load(file)['cities']
            cities = [city.lower() for city in cities]
    elif alpha_2 == 'us':
        subdivisions = pycountry.subdivisions.get(country_code='us')
        cities = [subdivision.name for subdivision in subdivisions]
    else:
        cities = []
    return {'cities': cities}


def get_universities_from_country(alpha_2: str = None) -> dict:
    universities = []
    if alpha_2 == 'fr':
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, FILE_FRENCH_UNIVERSITIES), 'r') as file:
            data = json.load(file)
            for d in data:
                uo_lib_officiel = d['fields']['uo_lib_officiel']
                if uo_lib_officiel not in universities:
                    universities.append(uo_lib_officiel)
                uo_lib = d['fields']['uo_lib']
                if uo_lib not in universities:
                    universities.append(uo_lib)
    return {'universities': universities}


def get_white_list_from_country(alpha_2: str = None) -> dict:
    alpha_2 = alpha_2.upper()
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_WHITE_LIST), 'r') as file:
        country_white_list = json.load(file)
        if alpha_2 in country_white_list.keys():
            white_list = country_white_list[alpha_2]
        else:
            white_list = []
    return {'white_list': white_list}


def get_stop_words_from_country(alpha_2: str = None) -> dict:
    alpha_2 = alpha_2.upper()
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, FILE_COUNTRY_FORBIDDEN), 'r') as file:
        country_stop_words = json.load(file)
        if alpha_2 in country_stop_words.keys():
            stop_words = country_stop_words[alpha_2]
        else:
            stop_words = []
    return {'stop_words': stop_words}


def init_country() -> None:
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    mapping = {'mappings': {'properties': {'universities': {'type': 'text'}}}}
    es.indices.create(index=ES_INDEX, body=mapping, ignore=400)
    es.delete_by_query(index=ES_INDEX, body={'query': {'match_all': {}}}, refresh=True)
    # TODO: use helpers.parallel_bulk
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {}
        info = get_info_from_country(country)
        body.update(info)
        cities = get_cities_from_country(country)
        body.update(cities)
        universities = get_universities_from_country(country)
        body.update(universities)
        white_list = get_white_list_from_country(country)
        body.update(white_list)
        stop_words = get_stop_words_from_country(country)
        body.update(stop_words)
        es.index(index=ES_INDEX, id=country, body=body, refresh=True)


if __name__ == '__main__':
    init_country()
