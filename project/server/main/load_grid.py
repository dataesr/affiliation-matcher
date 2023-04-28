import json
import os
import requests
import shutil

from elasticsearch.client import IndicesClient
from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.config import CHUNK_SIZE, GRID_DUMP_URL
from project.server.main.elastic_utils import get_analyzers, get_tokenizers, get_char_filters, get_filters, get_index_name, get_mappings
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import clean_list, ENGLISH_STOP, FRENCH_STOP, ACRONYM_IGNORED, GEO_IGNORED

logger = get_logger(__name__)
SOURCE = 'grid'

def download_data() -> dict:
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


def transform_data(data: dict) -> list:
    grids = data.get('institutes', [])
    res = []
    # Create a geonames dictionnary about the cities by region
    cities_by_region = {}
    ids = {}
    grids = data.get('institutes', [])
    for grid in grids:
        id = grid['id']
        for address in grid.get('addresses', []):
            country = address.get('country')
            city = address.get('city')
            if 'geonames_city' in address and address.get('geonames_city'):
                geonames_city = address.get('geonames_city')
                if 'geonames_admin1' in geonames_city and geonames_city.get('geonames_admin1'):
                    region = geonames_city.get('geonames_admin1').get('name')
            if region:
                if region not in cities_by_region:
                    cities_by_region[region] = []
                cities_by_region[region].append(city)
                ids[id] = {'region': region}
    # In the cities by region dictionnary, remove duplicated cities
    for region, cities in cities_by_region.items():
        cities_by_region[region] = list(set(cities_by_region[region]))
    for grid in grids:
        formatted_data = {'id': grid['id']}
        # Names
        names = [grid.get('name')]
        names += grid.get('aliases', [])
        names += [label.get('label') for label in grid.get('labels', [])]
        # Stop words is handled here as stop filter in ES keep track of positions even of removed stop words
        formatted_data['name'] = clean_list(data = names, stopwords = ENGLISH_STOP+FRENCH_STOP, min_token = 2)
        # Acronyms
        acronyms = grid.get('acronyms', [])
        formatted_data['acronym'] = clean_list(data = acronyms, ignored = ACRONYM_IGNORED, min_character = 2)
        # Countries, country_codes, regions, departments and cities
        countries, country_codes, regions, departments, cities = [], [], [], [], []
        for address in grid.get('addresses', []):
            country = address.get('country')
            countries.append(country)
            country_code = address.get('country_code').lower()
            country_codes.append(country_code)
            city = address.get('city')
            cities.append(city)
            if 'geonames_city' in address and address.get('geonames_city'):
                geonames_city = address.get('geonames_city')
                if 'geonames_admin1' in geonames_city and geonames_city.get('geonames_admin1'):
                    region = geonames_city.get('geonames_admin1').get('name')
                    regions.append(region)
                if 'nuts_level2' in geonames_city and geonames_city.get('nuts_level2'):
                    region = geonames_city.get('nuts_level2').get('name')
                    regions.append(region)
                if 'geonames_admin2' in geonames_city and geonames_city.get('geonames_admin2'):
                    department = geonames_city.get('geonames_admin2').get('name')
                    departments.append(department)
                if 'nuts_level3' in geonames_city and geonames_city.get('nuts_level3'):
                    department = geonames_city.get('nuts_level3').get('name')
                    departments.append(department)
                if 'city' in geonames_city and geonames_city.get('city'):
                    city = geonames_city.get('city')
                    cities.append(city)
        # Add country aliases
        if 'United Kingdom' in countries:
            countries.append('UK')
        elif 'United States' in countries:
            countries.append('USA')
        formatted_data['country'] = clean_list(data = countries)
        formatted_data['country_code'] = clean_list(data = country_codes)
        formatted_data['region'] = clean_list(data = regions, ignored = GEO_IGNORED)
        formatted_data['department'] = clean_list(data = departments, ignored = GEO_IGNORED)
        formatted_data['city'] = clean_list(data = cities, ignored = GEO_IGNORED)
        # Parents
        relationships = grid.get('relationships', [])
        formatted_data['parent'] = [relationship.get('id') for relationship in relationships if
                                    relationship.get('type') == 'Parent' and relationship.get('id')]
        if len(formatted_data['country_code']) == 0:
            continue
        formatted_data['country_alpha2'] = formatted_data['country_code']
        # Add the cities from the regions
        formatted_data['cities_by_region'] = []
        if regions:
            for r in regions:
                formatted_data['cities_by_region'] += cities_by_region.get(r, [])
            formatted_data['cities_by_region'] = clean_list(data = formatted_data['cities_by_region'], ignored=GEO_IGNORED)
        res.append(formatted_data)
    return res


def load_grid(index_prefix: str = 'matcher') -> dict:
    logger.debug('load grid ...')
    raw_data = download_data()
    transformed_data = transform_data(raw_data)
    
    es = MyElastic()
    # indices_client = IndicesClient(es)
    settings = {
        'analysis': {
            'char_filter': get_char_filters(),
            'tokenizer': get_tokenizers(),
            'filter': get_filters(),
            'analyzer': get_analyzers()
        }
    }
    criteria = ['id', 'acronym', 'cities_by_region', 'city', 'country',
                      'country_code', 'department', 'parent', 'region', 'name']
    criteria_unique = ['acronym', 'name']
    analyzers = {
        'id': 'light',
        'acronym': 'acronym_analyzer',
        'cities_by_region': 'light',
        'city': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'department': 'light',
        'name': 'heavy_en',
        'parent': 'light',
        'region': 'light'
    }
    for c in criteria_unique:
        criteria.append(f'{c}_unique')
        analyzers[f'{c}_unique'] = analyzers[c]
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    # Iterate over grid data
    for data_point in transformed_data:
        for criterion in criteria:
            criterion_values = data_point.get(criterion)
            if criterion_values is None:
                #logger.debug(f'This element {data_point} has no {criterion}')
                continue
            if not isinstance(criterion_values, list):
                criterion_values = [criterion_values]
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append({'id': data_point['id'], 'country_alpha2': data_point['country_alpha2']})
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
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            #if criterion in ['name']:
            #    tokens = get_tokens(indices_client, analyzer, index, criterion_value)
            #    if len(tokens) < 2:
            #        #logger.debug(f'Not indexing {criterion_value} (not enough token to be relevant !)')
            #        continue
            action = {
                    '_index': index,
                    'grids': [k['id'] for k in es_data[criterion][criterion_value]]
                    }
            for other_id in ['country_alpha2']:
                all_codes = [k.get(other_id) for k in es_data[criterion][criterion_value] if other_id in k]
                codes = list(set([j for sub in all_codes for j in sub]))
                if codes:
                    action[other_id] = codes
            action['query'] = {'match_phrase': {'content': {'query': criterion_value,
                                                                'analyzer': analyzer, 'slop': 0}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results
