import json
import os
import requests
import shutil

from elasticsearch.client import IndicesClient
from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.config import CHUNK_SIZE, GRID_DUMP_URL
from project.server.main.elastic_utils import get_analyzers, get_char_filters, get_filters, get_index_name, get_mappings
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import get_tokens, remove_stop, ENGLISH_STOP

logger = get_logger(__name__)
SOURCE = 'grid'


def download_grid_data() -> dict:
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


def transform_grid_data(data: dict) -> list:
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
        names = list(set(names))
        names = list(filter(None, names))
        # Stop words is handled here as stop filter in ES keep track of positions even of removed stop words
        formatted_data['name'] = [remove_stop(name, ENGLISH_STOP) for name in names]
        # Acronyms
        acronyms = grid.get('acronyms', [])
        acronyms = list(set(acronyms))
        formatted_data['acronym'] = list(filter(None, acronyms))
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
        countries = list(set(countries))
        country_codes = list(set(country_codes))
        regions = list(set(regions))
        departments = list(set(departments))
        cities = list(set(cities))
        formatted_data['country'] = list(filter(None, countries))
        formatted_data['country_code'] = list(filter(None, country_codes))
        formatted_data['region'] = list(filter(None, regions))
        formatted_data['department'] = list(filter(None, departments))
        formatted_data['city'] = list(filter(None, cities))
        # Parents
        relationships = grid.get('relationships', [])
        formatted_data['parent'] = [relationship.get('id') for relationship in relationships if
                                    relationship.get('type') == 'Parent' and relationship.get('id')]
        if len(formatted_data['country_code']) == 0:
            continue
        if len(formatted_data['country_code']) > 1:
            logger.debug(f'BEWARE: more than 1 country for {grid}. Only one is kept.')
        formatted_data['country_alpha2'] = formatted_data['country_code'][0]
        # Add the cities from the first founded region
        formatted_data['cities_by_region'] = []
        if len(countries) > 0 and len(regions) > 0:
            formatted_data['cities_by_region'] = cities_by_region.get(regions[0])
        res.append(formatted_data)
    return res


def load_grid(index_prefix: str = 'matcher') -> dict:
    es = MyElastic()
    indices_client = IndicesClient(es)
    settings = {
        'analysis': {
            'char_filter': get_char_filters(),
            'filter': get_filters(),
            'analyzer': get_analyzers()
        }
    }
    exact_criteria = ['acronym', 'cities_by_region', 'city', 'country',
                      'country_code', 'department', 'parent', 'region']
    txt_criteria = ['name']
    analyzers = {
        'acronym': 'acronym_analyzer',
        'cities_by_region': 'light',
        'city': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'department': 'light',
        'name': 'heavy_en',
        'parent': 'light',
        'region': 'light',
    }
    criteria = exact_criteria + txt_criteria
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    raw_grids = download_grid_data()
    grids = transform_grid_data(raw_grids)
    # Iterate over grid data
    for grid in grids:
        for criterion in criteria:
            criterion_values = grid.get(criterion)
            if criterion_values is None:
                logger.debug(f'This element {grid} has no {criterion}')
                continue
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append({'id': grid['id'], 'country_alpha2': grid['country_alpha2']})
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            if criterion in ['name']:
                tokens = get_tokens(indices_client, analyzer, index, criterion_value)
                if len(tokens) < 2:
                    logger.debug(f'Not indexing {criterion_value} (not enough token to be relevant !)')
                    continue
            action = {'_index': index, 'ids': [k['id'] for k in es_data[criterion][criterion_value]],
                      'country_alpha2': list(set([k['country_alpha2'] for k in es_data[criterion][criterion_value]]))}
            if criterion in criteria:
                action['query'] = {'match_phrase': {'content': {'query': criterion_value,
                                                                'analyzer': analyzer, 'slop': 0}}}
            # Do not add "USA" as grid acronym in order to not mix it together with the country alpha3
            if criterion != 'acronym' or criterion_value != 'USA':
                actions.append(action)
    es.parallel_bulk(actions=actions)
    return results