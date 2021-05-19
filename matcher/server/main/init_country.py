import json
import os
import pycountry
import requests

from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import get_data_from_grid

ES_INDEX = 'country'
FILE_FR_CITIES_INSEE = 'fr_cities_insee.csv'
FILE_FR_UNIVERSITIES_MESRI = 'fr_universities_mesri.json'
FILE_COUNTRY_FORBIDDEN = 'country_forbidden.json'
FILE_COUNTRY_WHITE_LIST = 'country_white_list.json'
QUERY_CITY_POPULATION_LIMIT = 50000
WIKIDATA_SPARQL_URL = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
GRID_DUMP_URL = 'https://ndownloader.figshare.com/files/27251693'

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
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
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
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
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
        logger.error('The request returned an error. Code : {code}'.format(code=response.status_code))
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


def get_info_from_country(alpha_2: str = None) -> dict:
    country = pycountry.countries.get(alpha_2=alpha_2)
    info = []
    if hasattr(country, 'name'):
        info.append(country.name)
    if hasattr(country, 'official_name'):
        info.append(country.official_name)
    if hasattr(country, 'common_name'):
        info.append(country.common_name)
    return {'alpha_2': country.alpha_2, 'alpha_3': country.alpha_3, 'info': info}


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


def get_all_from_grid():
    grids = get_data_from_grid(url=GRID_DUMP_URL)
    results = {}
    for grid in grids['institutes']:
        names = [grid.get('name')] + grid.get('aliases', [])
        acronyms = grid.get('acronyms', [])
        grid_addresses = grid.get('addresses', [])
        if len(grid_addresses) > 0:
            grid_address = grid_addresses[0]
            grid_country = grid_address.get('country_code').lower()
            if grid_country is not None and grid_country not in results.keys():
                results[grid_country] = {
                    'grid_cities': [],
                    'grid_hospitals_names': [],
                    'grid_hospitals_acronyms': [],
                    'grid_universities_names': [],
                    'grid_universities_acronyms': []
                }
            tmp_01 = grid_address.get('geonames_city', {}) if grid_address is not None else {}
            tmp_02 = tmp_01.get('geonames_admin1', {}) if tmp_01 is not None else {}
            address_02 = tmp_01.get('city') if tmp_01 is not None else None
            address_03 = tmp_02.get('name') if tmp_02 is not None else None
            grid_cities = [grid_address.get('city'), address_02, address_03]
            results[grid_country]['grid_cities'] += grid_cities
            for grid_type in grid.get('types', []):
                if grid_type == 'Healthcare':
                    results[grid_country]['grid_hospitals_names'] += names
                    results[grid_country]['grid_hospitals_acronyms'] += acronyms
                elif grid_type in ['Education', 'Facility']:
                    results[grid_country]['grid_universities_names'] += names
                    results[grid_country]['grid_universities_acronyms'] += acronyms
    return results


def init_country() -> None:
    es = MyElastic()
    mappings = {'mappings': {'properties': {'universities': {'type': 'text'}}}}
    es.create_index(index=ES_INDEX, mappings=mappings)
    wikidata_cities = get_cities_from_wikidata()
    wikidata_universities = get_universities_from_wikidata()
    wikidata_hospitals = get_hospitals_from_wikidata()
    grid = get_all_from_grid()
    actions = []
    for country in pycountry.countries:
        country = country.alpha_2.lower()
        body = {'_index': ES_INDEX}
        # GENERAL INFO
        info = get_info_from_country(country)
        body.update(info)
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
        # GRID HOSPITALS AND UNIVERSITIES
        body.update({
            'grid_cities': list(filter(None, list(set(grid.get(country, {}).get('grid_cities', []))))),
            'grid_hospitals_names': list(filter(None, list(set(grid.get(country, {})
                                                               .get('grid_hospitals_names', []))))),
            'grid_hospitals_acronyms': list(filter(None, list(set(grid.get(country, {})
                                                                  .get('grid_hospitals_acronyms', []))))),
            'grid_universities_names': list(filter(None, list(set(grid.get(country, {})
                                                                  .get('grid_universities_names', []))))),
            'grid_universities_acronyms': list(filter(None, list(set(grid.get(country, {})
                                                                     .get('grid_universities_acronyms', [])))))
        })
        # WHITE LIST
        body.update(get_white_list_from_country(country))
        # STOP WORDS
        body.update(get_stop_words_from_country(country))
        if country == 'fr':
            # INSEE CITIES
            body.update(get_cities_from_insee())
            # MESRI UNIVERSITIES
            body.update(get_universities_from_mesri())
        actions.append(body)
    es.parallel_bulk(actions=actions)


if __name__ == '__main__':
    init_country()
