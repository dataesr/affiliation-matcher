import pycountry

from project.server.main.elastic_utils import get_analyzers, get_tokenizers, get_char_filters, get_filters, get_index_name, get_mappings
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import COUNTRY_SWITCHER

SOURCE = 'country'

logger = get_logger(__name__)


def download_country_data():
    countries = [c.__dict__['_fields'] for c in list(pycountry.countries)]
    return countries


def transform_country_data(raw_data):
    subdivision_name, subdivision_code = {}, {}
    for subdivision in pycountry.subdivisions:
        alpha2 = subdivision.country_code.lower()
        if alpha2 not in subdivision_name:
            subdivision_name[alpha2] = []
        if alpha2 not in subdivision_code:
            subdivision_code[alpha2] = []
        subdivision_name[alpha2].append(subdivision.name)
        if alpha2 == 'us':
            subdivision_code[alpha2].append(subdivision.code[3:])
        if alpha2 == 'gb':
            subdivision_name[alpha2].append('northern ireland')
    countries = []
    for c in raw_data:
        # Alpha 2 - 3
        alpha2 = c['alpha_2'].lower()
        alpha3 = c['alpha_3'].lower()
        country = {'alpha2': alpha2, 'alpha3': [alpha3]}
        if alpha2 == 'gb':
            country['alpha3'].append('uk')
        # Names
        names = []
        for field_name in ['name', 'official_name', 'common_name']:
            if field_name in c:
                names.append(c[field_name])
        names += COUNTRY_SWITCHER.get(alpha2, [])
        names = list(set(names))
        country['name'] = names
        # Subdivisions
        if alpha2 in subdivision_name:
            country['subdivision_name'] = list(set(subdivision_name[alpha2]))
            country['subdivision_code'] = list(set(subdivision_code[alpha2]))
        countries.append(country)
    return countries


def load_country(index_prefix: str = 'matcher') -> dict:
    logger.debug('load country ...')
    es = MyElastic()
    settings = {
        'analysis': {
            'analyzer': get_analyzers(),
            'tokenizer': get_tokenizers(),
            'char_filter': get_char_filters(),
            'filter': get_filters()
        }
    }
    analyzers = {
        'name': 'name_analyzer',
        'subdivision_name': 'light',
        'subdivision_code': 'light',
        'alpha3': 'light'
    }
    criteria = list(analyzers.keys())
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    raw_countries = download_country_data()
    countries = transform_country_data(raw_countries)
    # Iterate over country data
    for country in countries:
        for criterion in criteria:
            criterion_values = country.get(criterion)
            criterion_values = criterion_values if isinstance(criterion_values, list) else [criterion_values]
            if criterion_values is None:
                logger.debug(f'This element {country} has no {criterion}')
                continue
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append({'country_alpha2': country['alpha2']})
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            if criterion_value:
                action = {'_index': index,
                          'country_alpha2': list(set([k['country_alpha2'] for k in
                                                      es_data[criterion][criterion_value]])),
                          'query': {
                              'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 2}}}}
                actions.append(action)
    es.parallel_bulk(actions=actions)
    return results
