import datetime

import requests

from matcher.server.main.config import SCANR_DUMP_URL
from matcher.server.main.elastic_utils import get_filters, get_analyzers
from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic

logger = get_logger(__name__)

SOURCE = 'rnsr'


def get_mappings(analyzer) -> dict:
    return {
        'properties': {
            'content': {
                'type': 'text',
                'analyzer': analyzer,
                'term_vector': 'with_positions_offsets'
            },
            'ids': {
                'type': 'text',
                'analyzer': 'keyword',
                'term_vector': 'with_positions_offsets'
            },
            'query': {
                'type': 'percolator'
            }
        }
    }


def init_rnsr(index_prefix: str = '') -> dict:
    es = MyElastic()
    settings = {
        'analysis': {
            'analyzer': get_analyzers(),
            'filter': get_filters(),
        }
    }
    light_criteria = ['city', 'acronym', 'code_number', 'supervisor_acronym', 'year']
    heavy_criteria = ['name', 'supervisor_name']
    criteria = light_criteria + heavy_criteria
    es_data = {}
    for criterion in criteria:
        index = f'{index_prefix}{SOURCE}_{criterion}'
        if criterion in light_criteria:
            mappings = get_mappings('light')
        else:
            mappings = get_mappings('heavy_fr')
        es.create_index(index=index, mappings=mappings, settings=settings)
        es_data[criterion] = {}
    rnsrs = download_rnsr_data()
    # Iterate over rnsr data
    for rnsr in rnsrs:
        for criterion in criteria:
            criterion_values = rnsr.get(criterion)
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append(rnsr['id'])
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        index = f'{index_prefix}{SOURCE}_{criterion}'
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            action = {'_index': index, 'ids': es_data[criterion][criterion_value]}
            if criterion in light_criteria:
                action['query'] = {
                    'match_phrase': {'content': {'query': criterion_value, 'analyzer': 'light', 'slop': 2}}}
            elif criterion in heavy_criteria:
                action['query'] = {'match': {'content': {'query': criterion_value, 'analyzer': 'heavy_fr',
                                                         'minimum_should_match': '4<80%'}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results


def download_rnsr_data() -> list:
    r = requests.get(SCANR_DUMP_URL)
    data = r.json()
    # todo : use rnsr key when available in dump rather than the regex
    # rnsr_regex = re.compile("[0-9]{9}[A-Z]")
    # rnsrs = [d for d in data if re.search(rnsr_regex, d['id'])]
    rnsrs = []
    for d in data:
        if 'rnsr' in [e['type'] for e in d.get('externalIds', [])]:
            rnsrs.append(d)
    logger.debug(f"{len(rnsrs)} rnsr elements detected in dump")
    # setting a dict with all names, acronyms and cities
    name_acronym_city = {}
    for d in data:
        current_id = d['id']
        name_acronym_city[current_id] = {}
        acronyms = []
        if d.get('acronym'):
            acronyms = list(set(d.get('acronym').values()))
        name_acronym_city[current_id]['acronym'] = list(filter(None, acronyms))
        names = []
        if d.get('label'):
            names = list(set(d.get('label', []).values()))
        if d.get('alias'):
            names += d.get('alias')
        names = list(set(names))
        name_acronym_city[current_id]['name'] = list(filter(None, names))
        cities = []
        for address in d.get('address', []):
            if 'city' in address and address['city']:
                cities.append(address['city'])
        name_acronym_city[current_id]['city'] = list(filter(None, cities))

    es_rnsrs = []
    for rnsr in rnsrs:
        rnsr_id = rnsr['id']
        es_rnsr = {'id': rnsr_id}
        # ACRONYMS & NAMES
        es_rnsr['acronym'] = name_acronym_city[rnsr_id]['acronym']
        es_rnsr['name'] = name_acronym_city[rnsr_id]['name']
        # CODE_NUMBERS
        code_numbers = []
        for code in [e['id'] for e in rnsr.get('externalIds', []) if e['type'] == 'label_numero']:
            code_numbers.extend([code, code.replace(' ', ''), code.replace(' ', '-'), code.replace(' ', '_')])
        es_rnsr['code_number'] = list(set(code_numbers))
        # SUPERVISORS ID
        es_rnsr['supervisor_id'] = [supervisor.get('structure') for supervisor in rnsr.get('institutions', [])
                                    if 'structure' in supervisor]
        es_rnsr['supervisor_id'] += [e['id'][0:9] for e in rnsr.get('externalIds', []) if "sire" in e['type']]
        es_rnsr['supervisor_id'] = list(set(es_rnsr['supervisor_id']))
        es_rnsr['supervisor_id'] = list(filter(None, es_rnsr['supervisor_id']))
        # SUPERVISORS ACRONYM, NAME AND CITY
        for f in ['acronym', 'name', 'city']:
            es_rnsr[f'supervisor_{f}'] = []
            for supervisor_id in es_rnsr['supervisor_id']:
                if supervisor_id in name_acronym_city:
                    es_rnsr[f'supervisor_{f}'] += name_acronym_city[supervisor_id][f'{f}']
            es_rnsr[f'supervisor_{f}'] = list(set(es_rnsr[f'supervisor_{f}']))
        # ADDRESSES
        es_rnsr['city'] = name_acronym_city[rnsr_id]['city']
        # DATES
        last_year = f'{datetime.date.today().year}'
        start_date = rnsr.get('startDate')
        if not start_date:
            start_date = '2010'
        start = int(start_date[0:4])
        end_date = rnsr.get('endDate')
        if not end_date:
            end_date = last_year
        end = int(end_date[0:4])
        # Start date one year before official as it can be used before sometimes
        es_rnsr['year'] = [str(y) for y in list(range(start - 1, end + 1))]
        es_rnsrs.append(es_rnsr)

    return es_rnsrs
