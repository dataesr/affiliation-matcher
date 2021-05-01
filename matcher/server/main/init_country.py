import json
import os
import pycountry
import requests

from elasticsearch import Elasticsearch
from matcher.server.main.config import config

ES_INDEX = 'country'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'
FILE_COUNTRY_WHITE_LIST = 'country_white_list.json'
FILE_FRENCH_UNIVERSITIES = 'fr_universities.json'
QUERY_CITY_POPULATION_LIMIT = 50000


def get_all_cities() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_official ?label_en ?label_fr ?label_es ?label_it WHERE { 
        ?city wdt:P31/wdt:P279* wd:Q515 ;
            wdt:P1082 ?population ;
            wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?city wdt:P1705 ?label_native . }
        OPTIONAL { ?city wdt:P1448 ?label_official . }
        OPTIONAL { ?city rdfs:label ?label_en filter (lang(?label_en) = "en") . }
        OPTIONAL { ?city rdfs:label ?label_fr filter (lang(?label_fr) = "fr") . }
        OPTIONAL { ?city rdfs:label ?label_es filter (lang(?label_es) = "es") . }
        OPTIONAL { ?city rdfs:label ?label_it filter (lang(?label_it) = "it") . }
        FILTER(?population > ''' + str(QUERY_CITY_POPULATION_LIMIT) + ''') .
    }
    '''
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    response = requests.get(url, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for city in response.json()['results']['bindings']:
            alpha_2 = city['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['strict'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_official' in city.keys():
                results[alpha_2]['strict'].append(city['label_official']['value'])
            elif 'label_en' in city.keys():
                results[alpha_2]['strict'].append(city['label_en']['value'])
            if 'label_native' in city.keys():
                results[alpha_2]['all'].append(city['label_native']['value'])
            if 'label_official' in city.keys():
                results[alpha_2]['all'].append(city['label_official']['value'])
            if 'label_en' in city.keys():
                results[alpha_2]['all'].append(city['label_en']['value'])
                results[alpha_2]['en'].append(city['label_en']['value'])
            if 'label_fr' in city.keys():
                results[alpha_2]['all'].append(city['label_fr']['value'])
                results[alpha_2]['fr'].append(city['label_fr']['value'])
            if 'label_es' in city.keys():
                results[alpha_2]['all'].append(city['label_es']['value'])
                results[alpha_2]['es'].append(city['label_es']['value'])
            if 'label_it' in city.keys():
                results[alpha_2]['all'].append(city['label_it']['value'])
                results[alpha_2]['it'].append(city['label_it']['value'])
    else:
        # TODO: use logger
        print('The request returned an error')
        print(response.status_code)
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'strict' in results[country].keys():
            results[country]['strict'] = list(set(results[country]['strict']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


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
    all_cities = get_all_cities()
    # TODO: use helpers.parallel_bulk
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {}
        info = get_info_from_country(country)
        body.update(info)
        cities_all = all_cities[country]['all'] if country in all_cities.keys() and 'all' in \
                                                                                    all_cities[country].keys() else []
        cities_strict = all_cities[country]['strict'] if country in all_cities.keys() and 'strict' in \
                                                                                    all_cities[country].keys() else []
        cities_en = all_cities[country]['en'] if country in all_cities.keys() and 'en' in all_cities[country].keys() \
            else []
        cities_fr = all_cities[country]['fr'] if country in all_cities.keys() and 'fr' in all_cities[country].keys() \
            else []
        cities_es = all_cities[country]['es'] if country in all_cities.keys() and 'es' in all_cities[country].keys() \
            else []
        cities_it = all_cities[country]['it'] if country in all_cities.keys() and 'it' in all_cities[country].keys() \
            else []
        body.update({'cities': cities_all, 'cities_strict': cities_strict,'cities_en': cities_en,
                     'cities_fr': cities_fr, 'cities_es': cities_es, 'cities_it': cities_it})
        universities = get_universities_from_country(country)
        body.update(universities)
        white_list = get_white_list_from_country(country)
        body.update(white_list)
        stop_words = get_stop_words_from_country(country)
        body.update(stop_words)
        es.index(index=ES_INDEX, id=country, body=body, refresh=True)


if __name__ == '__main__':
    init_country()
