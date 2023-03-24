import json
import os
import requests
import shutil

from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.config import CHUNK_SIZE, ROR_DUMP_URL
from project.server.main.elastic_utils import get_analyzers, get_char_filters, get_filters, get_index_name, get_mappings
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import download_insee_data, clean_list, ENGLISH_STOP, FRENCH_STOP, ACRONYM_IGNORED, GEO_IGNORED, NAME_IGNORED, COUNTRY_SWITCHER, CITY_COUNTRY

logger = get_logger(__name__)
SOURCE = 'ror'


def download_data() -> list:
    logger.debug('download ROR')
    ror_downloaded_file = 'ror_data_dump.zip'
    ror_unzipped_folder = mkdtemp()
    response = requests.get(url=ROR_DUMP_URL, stream=True)
    with open(file=ror_downloaded_file, mode='wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(file=ror_downloaded_file, mode='r') as file:
        file.extractall(ror_unzipped_folder)
    for data_file in os.listdir(ror_unzipped_folder):
        if data_file.endswith('.json'):
            with open(f'{ror_unzipped_folder}/{data_file}', 'r') as file:
                data = json.load(file)
    os.remove(path=ror_downloaded_file)
    shutil.rmtree(path=ror_unzipped_folder)
    return data

def get_external_ids(external):
    ids = []
    for k in external:
        if isinstance(external[k], list):
            ids += external[k]
        elif isinstance(external[k], str):
            ids.append(external[k])
    return list(set(ids))

def build_zone_mapping(rors):
    zone_composition = {}
    city_zone = {}
    for zone_code_label in ['nuts_level1', 'nuts_level2', 'nuts_level3', 'zone_emploi']:
        city_zone[zone_code_label] = {}
    for d in rors:
        for address in d.get('addresses', []):
            #city = address.get('city')
            if 'geonames_city' not in address:
                continue
            geoname = address['geonames_city']
            city = None
            if geoname.get('id'):
                city_code = str(geoname['id'])
                city = geoname['city']
            if not city:
                continue
            for zone_code_label in ['nuts_level1', 'nuts_level2', 'nuts_level3', 'zone_emploi']:
                zone_code = geoname.get(zone_code_label, {}).get('code')
                if zone_code is None:
                    continue
                zone_code = str(zone_code)
                if zone_code not in zone_composition:
                    zone_composition[zone_code] = []
                zone_composition[zone_code].append(city)
                if city_code not in city_zone[zone_code_label]:
                    city_zone[zone_code_label][city_code] = []
                if zone_code and zone_code not in city_zone[zone_code_label][city_code]:
                    city_zone[zone_code_label][city_code].append(zone_code)
                assert(len(city_zone[zone_code_label][city_code]) <= 1)
    for zone_code in zone_composition:
        zone_composition[zone_code] = clean_list(zone_composition[zone_code])
    return zone_composition, city_zone

def transform_data(rors: list) -> list:
    logger.debug('transform data')
    # adding zone emploi data for France ie Saint Martin d'hères <-> Grenoble
    zone_emploi_insee = download_insee_data()
    zone_emploi_dict ={}
    for e in zone_emploi_insee:
        dict_key = e['DEP']+';'+e['LIBGEO']
        if dict_key not in zone_emploi_dict:
            zone_emploi_dict[dict_key] = {'code': 'ZE2020_'+str(e['ZE2020']), 'name': e['LIBZE2020']}
        else:
            pass
    for e in rors:
        if isinstance(e.get('addresses'), list):
            for address in e['addresses']:
                if address.get('geonames_city', {}).get('geonames_admin2', {}).get('code'):
                    city = address.get('city')
                    code = address.get('geonames_city', {}).get('geonames_admin2', {}).get('code')
                    if city and code and code[0:2]=='FR':
                        departement = code.split('.')[-1]
                        dict_key = departement+';'+city
                        if dict_key not in zone_emploi_dict:
                            logger.debug(f"WARNING ! wrong french city name for {e['id']} key {dict_key} not in INSEE zone emploi")
                        else:
                            address['geonames_city']['zone_emploi'] = zone_emploi_dict[dict_key]


    zone_composition, city_zone = build_zone_mapping(rors)
    data = []
    for ror in rors:
        current_id = ror.get('id').replace('https://ror.org/', '')
        acronym = ror.get('acronyms', [])
        city = [address.get('city') for address in ror.get('addresses', [])]
        current_zone_cities = {}
        for address in ror.get('addresses', []):
            geoname = address.get('geonames_city')
            if geoname and 'id' in geoname and geoname.get('id'):
                city_code = str(geoname['id'])
                for zone_code_label in ['nuts_level1', 'nuts_level2', 'nuts_level3', 'zone_emploi']:
                    if city_code in city_zone[zone_code_label] and city_zone[zone_code_label][city_code]:
                        current_zone_code = city_zone[zone_code_label][city_code][0]
                        if current_zone_code in zone_composition:
                            current_zone_cities[zone_code_label] = zone_composition[current_zone_code]

        country = [ror.get('country', {}).get('country_name')]
        country_code = [ror.get('country', {}).get('country_code').lower()]
        for c in country_code:
            current_code = c.lower()
            if current_code in COUNTRY_SWITCHER:
                country += COUNTRY_SWITCHER[current_code]
        for c in city:
            country += CITY_COUNTRY.get(c.lower(), [])

        name = [ror.get('name')]
        name += ror.get('aliases', [])
        name += [label.get('label') for label in ror.get('labels', [])]
        names_to_add = []
        for n in name:
            if n[0:11].lower()=='university ':
                names_to_add.append(n[11:]+' university')
                names_to_add.append(n[11:])
            if n[-11:].lower()==' university':
                names_to_add.append('university '+n[:-11])
                names_to_add.append(n[:-11])
        name += names_to_add
        externals = ror.get('external_ids', [])
        external_ids = {}
        grids = []
        for ext_id in list(externals.keys()):
            external_ids[ext_id.lower()+'s'] = get_external_ids(externals[ext_id])
            if ext_id.lower() == 'grid':
                grids = get_external_ids(externals[ext_id])
        countries_code = clean_list(data=country_code)
        current_data = {
            'acronym': clean_list(data=acronym, ignored=ACRONYM_IGNORED, min_character = 2),
            'city': clean_list(data=city, ignored=GEO_IGNORED),
            'country': clean_list(data=country),
            'country_code': countries_code,
            'id': current_id,
            'name': clean_list(data=name, stopwords=FRENCH_STOP+ENGLISH_STOP, min_token = 2),
        }
        #for zone_code_label in ['nuts_level1', 'nuts_level2', 'nuts_level3']:
        for zone_code_label in ['nuts_level2', 'zone_emploi']:
            if zone_code_label in current_zone_cities and current_zone_cities[zone_code_label]:
                current_data[f'city_{zone_code_label}'] = current_zone_cities[zone_code_label]
        if grids:
            current_data['grid_id'] = grids
        if external_ids:
            current_data['external_ids'] = external_ids
        supervisor_name = []
        relationships = ror.get('relationships')
        if relationships:
            for relationship in relationships:
                if relationship.get('type') == 'Parent' and relationship.get('label'):
                    supervisor_name.append(relationship.get('label'))
        current_data['supervisor_name'] = clean_list(data=supervisor_name, stopwords=FRENCH_STOP+ENGLISH_STOP, min_token = 2)
        data.append(current_data)
    return data
        
def load_ror(index_prefix: str = 'matcher') -> dict:
    logger.debug('load ROR start')
    raw_data = download_data()
    transformed_data = transform_data(raw_data)
    # Init ES
    es_data = {}
    es = MyElastic()
    settings = {
        'analysis': {
            'analyzer': get_analyzers(),
            'char_filter': get_char_filters(),
            'filter': get_filters()
        }
    }
    analyzers = {
        'id': 'light',
        'grid_id': 'light',
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'city_zone_emploi': 'city_analyzer',
        'city_nuts_level1': 'city_analyzer',
        'city_nuts_level2': 'city_analyzer',
        'city_nuts_level3': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'name': 'heavy_en',
        'supervisor_name': 'heavy_en'
    }
    criteria = ['id', 'grid_id', 'acronym', 'city', 'country', 'country_code', 'name', 'supervisor_name', 'city_nuts_level1', 'city_nuts_level2', 'city_nuts_level3', 'city_zone_emploi']
    criteria_unique = ['acronym', 'name']
    for c in criteria_unique:
        criteria.append(f'{c}_unique')
        analyzers[f'{c}_unique'] = analyzers[c]
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    external_ids_label = []
    # Iterate over ror data
    logger.debug('iterating over data points')
    for data_point in transformed_data:
        for criterion in criteria:
            criterion_values = data_point.get(criterion)
            if criterion_values is None:
                logger.debug(f'This element {data_point} has no {criterion}')
                continue
            if not isinstance(criterion_values, list):
                criterion_values = [criterion_values]
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                current_elt = { 
                    'id': data_point.get('id'),
                    'country_alpha2': data_point.get('country_code')
                }
                for ext_id in data_point.get('external_ids', {}):
                    current_elt[ext_id] = data_point['external_ids'][ext_id]
                    if ext_id not in external_ids_label:
                        external_ids_label.append(ext_id)
                es_data[criterion][criterion_value].append(current_elt)
    # add unique criterion
    for criterion in criteria_unique:
        for criterion_value in es_data[criterion]:
            if len(es_data[criterion][criterion_value]) == 1:
                if f'{criterion}_unique' not in es_data:
                    es_data[f'{criterion}_unique'] = {}
                es_data[f'{criterion}_unique'][criterion_value] = es_data[criterion][criterion_value]
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        logger.debug(f'prep index {criterion}')
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            action = {
                '_index': index,
                'rors': [k['id'] for k in es_data[criterion][criterion_value]],
            }
            for other_id in ['country_alpha2', 'grids', 'rors', 'wikidatas']:
                all_codes = [k.get(other_id) for k in es_data[criterion][criterion_value] if other_id in k]
                codes = list(set([j for sub in all_codes for j in sub]))
                if codes:
                    action[other_id] = codes
            if criterion in criteria:
                action['query'] = {'match_phrase': {'content': {'query': criterion_value,
                                                                'analyzer': analyzer, 'slop': 0}}}
            actions.append(action)
    logger.debug('bulk insert')
    es.parallel_bulk(actions=actions)
    return results
