import pycountry

from matcher.server.main.logger import get_logger
from matcher.server.main.elastic_utils import get_filters, get_analyzers, get_char_filters, get_index_name, get_mappings
from matcher.server.main.my_elastic import MyElastic

SOURCE = 'country'

logger = get_logger(__name__)

def download_country_data():
    countries = [c.__dict__['_fields'] for c in list(pycountry.countries)]
    return countries

def transform_country_data(raw_data):
    countries = []
    for c in raw_data:
        # ALPHA 2 - 3
        country = {'alpha2': c['alpha_2'].lower(), 'alpha3': [c['alpha_3']]}
        # NAMES
        all_names = []
        for field_name in ['name', 'official_name', 'common_name']:
            if field_name in c:
                all_names.append(c[field_name])
        all_names = list(set(all_names))
        country['all_names'] = all_names
        if 'name' in c:
            country['name'] = c['name']
        countries.append(country)
    return countries

def load_country(index_prefix: str = '') -> None:
    es = MyElastic()
    settings = {
        'analysis': {
            'char_filter': get_char_filters(),
            'filter': get_filters(),
            'analyzer': get_analyzers()
        }
    }
    analyzers = {
        'all_names': 'country_analyzer',
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
            if criterion_values is None:
                logger.debug(f"This element {country} has no {criterion}")
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
            action = {'_index': index, 'country_alpha2': list(set([k['country_alpha2'] for k in es_data[criterion][criterion_value]]))}
            action['query'] = {
                'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 2}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results
