from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import download_data_from_grid

SOURCE = 'grid'

es = MyElastic()


def init_grid(index_prefix: str = '') -> None:
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
    index_cities = f'{index_prefix}{SOURCE}_cities'
    index_institutions = f'{index_prefix}{SOURCE}_institutions'
    index_institutions_acronyms = f'{index_prefix}{SOURCE}_institutions_acronyms'
    indexes = [index_cities, index_institutions, index_institutions_acronyms]
    for index in indexes:
        es.create_index(index=index, mappings=mappings)
    data = download_data_from_grid()
    grids = data.get('institutes', [])
    # Iterate over grid data
    es_data = {}
    for grid in grids:
        institutions = [grid.get('name')]
        institutions += grid.get('aliases', [])
        institutions += [label.get('label') for label in grid.get('labels', [])]
        acronyms = grid.get('acronyms', [])
        for address in grid.get('addresses', []):
            country_code = address.get('country_code').lower()
            if country_code not in es_data:
                es_data[country_code] = {'cities': [], 'institutions': [], 'acronyms': []}
            es_data[country_code]['institutions'] += institutions
            es_data[country_code]['acronyms'] += acronyms
            es_data[country_code]['cities'].append(address.get('city'))
            if address.get('geonames_city', {}):
                es_data[country_code]['cities'].append(address.get('geonames_city', {}).get('city'))
    # Bulk insert data into ES
    actions = []
    for country_alpha2 in es_data:
        action_template = {'_index': index_cities, 'country_alpha2': country_alpha2}
        cities = list(set(es_data[country_alpha2]['cities']))
        for query in cities:
            action = action_template.copy()
            action.update({'query': {'match_phrase': {'content': {'query': query, 'analyzer': 'standard'}}}})
            actions.append(action)
        action_template = {'_index': index_institutions, 'country_alpha2': country_alpha2}
        institutions = list(set(es_data[country_alpha2]['institutions']))
        for query in institutions:
            action = action_template.copy()
            action.update({'query': {'match_phrase': {'content': {'query': query, 'analyzer': 'standard'}}}})
            actions.append(action)
        action_template = {'_index': index_institutions_acronyms, 'country_alpha2': country_alpha2}
        acronyms = list(set(es_data[country_alpha2]['acronyms']))
        for query in acronyms:
            action = action_template.copy()
            action.update({'query': {'match_phrase': {'content': {'query': query, 'analyzer': 'standard'}}}})
            actions.append(action)
    es.parallel_bulk(actions=actions)
