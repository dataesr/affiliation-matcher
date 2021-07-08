from matcher.server.main.elastic_utils import get_analyzers, get_char_filters, get_filters, get_index_name, get_mappings
from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import download_grid_data

logger = get_logger(__name__)

SOURCE = 'grid'


def load_grid(index_prefix: str = '') -> dict:
    es = MyElastic()
    settings = {
        'analysis': {
            'char_filter': get_char_filters(),
            'filter': get_filters(),
            'analyzer': get_analyzers()
        }
    }
    exact_criteria = ['acronym', 'city', 'country', 'country_code']
    txt_criteria = ['name']
    analyzers = {
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'name': 'heavy_en'
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
            action = {'_index': index, 'ids': [k['id'] for k in es_data[criterion][criterion_value]],
                      'country_alpha2': list(set([k['country_alpha2'] for k in es_data[criterion][criterion_value]]))}
            if criterion in exact_criteria:
                action['query'] = {
                    'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 2}}}
            elif criterion in txt_criteria:
                action['query'] = {'match': {'content': {'query': criterion_value, 'analyzer': analyzer,
                                                         'minimum_should_match': '-20%'}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results


def transform_grid_data(data):
    grids = data.get('institutes', [])
    res = []
    for grid in grids:
        formatted_data = {'id': grid['id']}
        # Names
        institutions = [grid.get('name')]
        institutions += grid.get('aliases', [])
        institutions += [label.get('label') for label in grid.get('labels', [])]
        institutions = list(set(institutions))
        formatted_data['name'] = list(filter(None, institutions))
        # Acronyms
        acronyms = grid.get('acronyms', [])
        acronyms = list(set(acronyms))
        formatted_data['acronym'] = list(filter(None, acronyms))
        # countries, country_codes and cities
        countries, country_codes, cities = [], [], []
        for address in grid.get('addresses', []):
            country = address.get('country')
            countries.append(country)
            country_code = address.get('country_code').lower()
            country_codes.append(country_code)
            city1 = address.get('city')
            cities.append(city1)
            if address.get('geonames_city', {}):
                city2 = address.get('geonames_city', {}).get('city')
                cities.append(city2)
        countries = list(set(countries))
        country_codes = list(set(country_codes))
        cities = list(set(cities))
        formatted_data['country'] = list(filter(None, countries))
        formatted_data['country_code'] = list(filter(None, country_codes))
        formatted_data['city'] = list(filter(None, cities))
        if len(formatted_data['country_code']) == 0:
            continue
        if len(formatted_data['country_code']) > 1:
            logger.debug(f'BEWARE: more than 1 country for {grid}')
            logger.debug(f'Only one is kept')
        formatted_data['country_alpha2'] = formatted_data['country_code'][0]
        res.append(formatted_data)
    return res
