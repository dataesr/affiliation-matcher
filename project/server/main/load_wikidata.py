import requests

from project.server.main.elastic_utils import get_index_name
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic

QUERY_CITY_POPULATION_LIMIT = 50000
SOURCE = 'wikidata'
WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'

es = MyElastic()
logger = get_logger(__name__)


def get_cities_from_wikidata() -> list:
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
    if response.status_code == requests.codes.ok:
        results = response.json()['results']['bindings']
    else:
        logger.error(f'The request returned an error. Code : {response.status_code}')
        results = []
    return results


def get_universities_from_wikidata() -> list:
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
    if response.status_code == requests.codes.ok:
        results = response.json()['results']['bindings']
    else:
        logger.error(f'The request returned an error. Code : {response.status_code}')
        results = []
    return results


def get_hospitals_from_wikidata() -> list:
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
    if response.status_code == requests.codes.ok:
        results = response.json()['results']['bindings']
    else:
        logger.error(f'The request returned an error. Code : {response.status_code}')
        results = []
    return results


def data2actions(index: str, data: list = None) -> list:
    if data is None:
        data = []
    actions = []
    es_data = {}
    for d in data:
        country_code = d.get('country_alpha2', {}).get('value').lower()
        if country_code not in es_data:
            es_data[country_code] = []
        names = [
            d.get('label_en', {}).get('value'),
            d.get('label_es', {}).get('value'),
            d.get('label_fr', {}).get('value'),
            d.get('label_it', {}).get('value'),
            d.get('label_native', {}).get('value'),
            d.get('label_official', {}).get('value')
        ]
        es_data[country_code] += names
    # Bulk insert wikidata cities into ES
    for country_alpha2 in es_data:
        action_template = {'_index': index, 'country_alpha2': country_alpha2}
        data = list(filter(None, list(set(es_data[country_alpha2]))))
        for query in data:
            action = action_template.copy()
            action.update({'query': {'match_phrase': {'content': {'query': query, 'analyzer': 'standard'}}}})
            actions.append(action)
    return actions


def load_wikidata(index_prefix: str = '') -> dict:
    mappings = {
        'properties': {
            'content': {
                'type': 'text',
                'analyzer': 'standard',
                'term_vector': 'with_positions_offsets'
            },
            'country': {
                'type': 'text',
                'analyzer': 'standard',
                'term_vector': 'with_positions_offsets'
            },
            'query': {
                'type': 'percolator'
            }
        }
    }
    index_city = get_index_name(index_name='city', source=SOURCE, index_prefix=index_prefix)
    index_hospital = get_index_name(index_name='hospital', source=SOURCE, index_prefix=index_prefix)
    index_university = get_index_name(index_name='university', source=SOURCE, index_prefix=index_prefix)
    indexes = [index_city, index_university, index_hospital]
    results = {}
    for index in indexes:
        es.create_index(index=index, mappings=mappings)
    actions = []
    cities = get_cities_from_wikidata()
    actions += data2actions(data=cities, index=index_city)
    results[index_city] = len(cities)
    hospitals = get_hospitals_from_wikidata()
    actions += data2actions(data=hospitals, index=index_hospital)
    results[index_hospital] = len(hospitals)
    universities = get_universities_from_wikidata()
    actions += data2actions(data=universities, index=index_university)
    results[index_university] = len(universities)
    es.parallel_bulk(actions=actions)
    return results
