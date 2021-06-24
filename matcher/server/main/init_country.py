import json
import os

import pycountry
import requests

from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic

ES_INDEX = 'country'
FILE_FR_CITIES_INSEE = 'fr_cities_insee.csv'
FILE_FR_UNIVERSITIES_MESRI = 'fr_universities_mesri.json'
QUERY_CITY_POPULATION_LIMIT = 50000
WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'

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


def get_cities_from_wikidata() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_official ?label_en ?label_fr ?label_es ?label_it WHERE { 
        ?city wdt:P31/wdt:P279* wd:Q515 ;
            wdt:P1082 ?population ;
            wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?city wdt:P1705 ?label_native . }
        OPTIONAL { ?city wdt:P1448 ?label_official . }
        OPTIONAL { ?city rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?city rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?city rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?city rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
        FILTER(?population > ''' + str(QUERY_CITY_POPULATION_LIMIT) + ''') .
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
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
        logger.error(f'The request returned an error. Code : {response.status_code}')
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


def get_universities_from_wikidata() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_en ?label_fr ?label_es ?label_it WHERE {
        ?university wdt:P31/wdt:P279* wd:Q38723 ;
                  wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?university wdt:P1705 ?label_native . }
        OPTIONAL { ?university rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?university rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?university rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?university rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for university in response.json()['results']['bindings']:
            alpha_2 = university['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_native' in university.keys():
                results[alpha_2]['all'].append(university['label_native']['value'])
            if 'label_en' in university.keys():
                results[alpha_2]['all'].append(university['label_en']['value'])
                results[alpha_2]['en'].append(university['label_en']['value'])
            if 'label_fr' in university.keys():
                results[alpha_2]['all'].append(university['label_fr']['value'])
                results[alpha_2]['fr'].append(university['label_fr']['value'])
            if 'label_es' in university.keys():
                results[alpha_2]['all'].append(university['label_es']['value'])
                results[alpha_2]['es'].append(university['label_es']['value'])
            if 'label_it' in university.keys():
                results[alpha_2]['all'].append(university['label_it']['value'])
                results[alpha_2]['it'].append(university['label_it']['value'])
    else:
        logger.error(f'The request returned an error. Code : {response.status_code}')
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


def get_hospitals_from_wikidata() -> dict:
    query = '''
    SELECT DISTINCT ?country_alpha2 ?label_native ?label_en ?label_fr ?label_es ?label_it WHERE {
        ?hospital wdt:P31/wdt:P279* wd:Q16917 ;
                wdt:P17 ?country .
        ?country wdt:P297 ?country_alpha2 .
        OPTIONAL { ?hospital wdt:P1705 ?label_native . }
        OPTIONAL { ?hospital rdfs:label ?label_en FILTER(lang(?label_en) = "en") . }
        OPTIONAL { ?hospital rdfs:label ?label_fr FILTER(lang(?label_fr) = "fr") . }
        OPTIONAL { ?hospital rdfs:label ?label_es FILTER(lang(?label_es) = "es") . }
        OPTIONAL { ?hospital rdfs:label ?label_it FILTER(lang(?label_it) = "it") . }
    }
    '''
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query, 'format': 'json'})
    results = {}
    if response.status_code == requests.codes.ok:
        for hospital in response.json()['results']['bindings']:
            alpha_2 = hospital['country_alpha2']['value'].lower()
            if alpha_2 not in results.keys():
                results[alpha_2] = {}
                results[alpha_2]['all'] = []
                results[alpha_2]['en'] = []
                results[alpha_2]['fr'] = []
                results[alpha_2]['es'] = []
                results[alpha_2]['it'] = []
            if 'label_native' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_native']['value'])
            if 'label_en' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_en']['value'])
                results[alpha_2]['en'].append(hospital['label_en']['value'])
            if 'label_fr' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_fr']['value'])
                results[alpha_2]['fr'].append(hospital['label_fr']['value'])
            if 'label_es' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_es']['value'])
                results[alpha_2]['es'].append(hospital['label_es']['value'])
            if 'label_it' in hospital.keys():
                results[alpha_2]['all'].append(hospital['label_it']['value'])
                results[alpha_2]['it'].append(hospital['label_it']['value'])
    else:
        logger.error(f'The request returned an error. Code : {response.status_code}')
    for country in results:
        results[country]['all'] = list(set(results[country]['all']))
        if 'en' in results[country].keys():
            results[country]['en'] = list(set(results[country]['en']))
        if 'fr' in results[country].keys():
            results[country]['fr'] = list(set(results[country]['fr']))
        if 'es' in results[country].keys():
            results[country]['es'] = list(set(results[country]['es']))
        if 'it' in results[country].keys():
            results[country]['it'] = list(set(results[country]['it']))
    return results


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
                },
                'country_filter': {
                    'type': 'stop',
                    'ignore_case': True,
                    'stopwords': ['france']
                }
            },
            'analyzer': {
                'analyzer_name': {
                    'tokenizer': 'icu_tokenizer',
                    'filter': ['length_min_3_char']
                },
                'analyzer_cities': {
                    'tokenizer': 'icu_tokenizer',
                    'filter': ['country_filter', 'icu_folding', 'length_min_3_char', 'lowercase']
                }
            }
        }
    }
    mappings = {
        'properties': {
            'all_names': {
                'type': 'text',
                'analyzer': 'analyzer_name'
            },
            'wikidata_cities': {
                'type': 'text',
                'analyzer': 'analyzer_cities'
            },
            'wikidata_hospitals': {
                'type': 'text',
                'analyzer': 'analyzer_name'
            },
            'grid_cities': {
                'type': 'text',
                'analyzer': 'analyzer_cities'
            }
        }
    }
    es.create_index(index=index, settings=settings, mappings=mappings)
    wikidata_cities = get_cities_from_wikidata()
    wikidata_universities = get_universities_from_wikidata()
    wikidata_hospitals = get_hospitals_from_wikidata()
    actions = []
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {'_index': index}
        # GENERAL NAMES
        names = get_names_from_country(alpha_2=country)
        body.update(names)
        # WIKIDATA CITIES
        body.update({
            'wikidata_cities': wikidata_cities.get(country, {}).get('all', []),
            'wikidata_cities_strict': wikidata_cities.get(country, {}).get('strict', []),
            'wikidata_cities_en': wikidata_cities.get(country, {}).get('en', []),
            'wikidata_cities_fr': wikidata_cities.get(country, {}).get('fr', []),
            'wikidata_cities_es': wikidata_cities.get(country, {}).get('es', []),
            'wikidata_cities_it': wikidata_cities.get(country, {}).get('it', [])
        })
        # WIKIDATA UNIVERSITIES
        body.update({
            'wikidata_universities': wikidata_universities.get(country, {}).get('all', []),
            'wikidata_universities_en': wikidata_universities.get(country, {}).get('en', []),
            'wikidata_universities_fr': wikidata_universities.get(country, {}).get('fr', []),
            'wikidata_universities_es': wikidata_universities.get(country, {}).get('es', []),
            'wikidata_universities_it': wikidata_universities.get(country, {}).get('it', [])
        })
        # WIKIDATA HOSPITALS
        body.update({
            'wikidata_hospitals': wikidata_hospitals.get(country, {}).get('all', []),
            'wikidata_hospitals_en': wikidata_hospitals.get(country, {}).get('en', []),
            'wikidata_hospitals_fr': wikidata_hospitals.get(country, {}).get('fr', []),
            'wikidata_hospitals_es': wikidata_hospitals.get(country, {}).get('es', []),
            'wikidata_hospitals_it': wikidata_hospitals.get(country, {}).get('it', [])
        })
        if country == 'fr':
            # INSEE CITIES
            body.update(get_cities_from_insee())
            # MESRI UNIVERSITIES
            body.update(get_universities_from_mesri())
        actions.append(body)
    es.parallel_bulk(actions=actions)
