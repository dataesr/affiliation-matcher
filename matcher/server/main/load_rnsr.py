import datetime

import requests

from matcher.server.main.config import SCANR_DUMP_URL
from matcher.server.main.elastic_utils import get_filters, get_analyzers, get_char_filters, get_index_name, get_mappings
from matcher.server.main.logger import get_logger
from matcher.server.main.my_elastic import MyElastic
from matcher.server.main.utils import get_alpha2_from_french, download_insee_data

logger = get_logger(__name__)

SOURCE = 'rnsr'


def load_rnsr(index_prefix: str = '') -> dict:
    es = MyElastic()
    settings = {
        'analysis': {
            'char_filter': get_char_filters(),
            'filter': get_filters(),
            'analyzer': get_analyzers()
        }
    }
    exact_criteria = ['city', 'urban_unit', 'country_code', 'acronym', 'code_number', 'supervisor_acronym', 'year']
    txt_criteria = ['name', 'supervisor_name']
    analyzers = {
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'urban_unit': 'city_analyzer',
        'country_code': 'light',
        'code_number': 'code_analyzer',
        'name': 'heavy_fr',
        'supervisor_acronym': 'acronym_analyzer',
        'supervisor_name': 'heavy_fr',
        'year': 'light',
    }
    criteria = exact_criteria + txt_criteria
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    raw_rnsrs = download_rnsr_data()
    rnsrs = transform_rnsr_data(raw_rnsrs)
    # Iterate over rnsr data
    for rnsr in rnsrs:
        for criterion in criteria:
            criterion_values = rnsr.get(criterion)
            if criterion_values is None:
                logger.debug(f"This element {rnsr} has no {criterion}")
                continue
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append({'id': rnsr['id'], 'country_alpha2': rnsr['country_alpha2']})
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            action = {'_index': index, 'ids': [k['id'] for k in es_data[criterion][criterion_value]], 'country_alpha2': list(set([k['country_alpha2'] for k in es_data[criterion][criterion_value]]))}
            if criterion in exact_criteria:
                action['query'] = {
                    'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 2}}}
            elif criterion in txt_criteria:
                action['query'] = {'match': {'content': {'query': criterion_value, 'analyzer': analyzer,
                                                         'minimum_should_match': '-20%'}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results


def get_values(x: dict) -> list:
    if x.get('fr', '') == x.get('en', '') and x.get('fr'):
        return [x['fr']]
    if (x.get('en', '') in x.get('default', '')) and (x.get('fr', '') in x.get('default', '')) and 'default' in x:
        del x['default']
    return list(set(x.values()))


def download_rnsr_data() -> list:
    r = requests.get(SCANR_DUMP_URL)
    data = r.json()
    return data

def transform_rnsr_data(data) -> list:
    # todo : use rnsr key when available in dump rather than the regex
    # rnsr_regex = re.compile("[0-9]{9}[A-Z]")
    # rnsrs = [d for d in data if re.search(rnsr_regex, d['id'])]
    rnsrs = []
    for d in data:
        external_ids = d.get('externalIds', [])
        if 'rnsr' in [e['type'] for e in external_ids]:
            d['rnsr'] = [e['id'] for e in external_ids if e['type'] == 'rnsr'][0]
            rnsrs.append(d)
    logger.debug(f'{len(rnsrs)} rnsr elements detected in dump')
    # setting a dict with all names, acronyms and cities
    name_acronym_city = {}
    urban_unit_composition = {}
    for d in data:
        current_id = d['id']
        name_acronym_city[current_id] = {}
        # ACRONYMS
        acronyms = []
        if d.get('acronym'):
            acronyms = get_values(d.get('acronym', []))
        # NAMES
        names = []
        if d.get('label'):
            names += get_values(d.get('label', []))
        if d.get('alias'):
            names += d.get('alias')
        names = list(set(names))
        names = list(set(names) - set(acronyms))
        # CITIES, COUNTRIES
        cities, country_alpha2, urbanUnits = [], [], []
        for address in d.get('address', []):
            if 'city' in address and address['city']:
                cities.append(address['city'])
            if 'urbanUnitLabel' in address and address['urbanUnitLabel']:
                urbanUnits.append(address['urbanUnitLabel'])
            if 'country' in address and address['country']:
                alpha2 = get_alpha2_from_french(address['country'])
                country_alpha2.append(alpha2)
            if 'city' in address and address['city'] and 'urbanUnitLabel' in address and address['urbanUnitLabel']:
                city = address['city']
                urban_unit = address['urbanUnitLabel']
                if urban_unit not in urban_unit_composition:
                    urban_unit_composition[urban_unit] = []
                if city not in urban_unit_composition[urban_unit]:
                    urban_unit_composition[urban_unit].append(city)

        cities = list(set(cities))
        country_alpha2 = list(set(country_alpha2))
        urbanUnits = list(set(urbanUnits))
        name_acronym_city[current_id]['city'] = list(filter(None, cities))
        name_acronym_city[current_id]['urban_unit'] = list(filter(None, urbanUnits))
        name_acronym_city[current_id]['acronym'] = list(filter(None, acronyms))
        name_acronym_city[current_id]['name'] = list(filter(None, names))
        country_alpha2 = list(filter(None, country_alpha2))
        if not country_alpha2:
            country_alpha2 = ['fr']
        name_acronym_city[current_id]['country_alpha2'] = country_alpha2[0] 

    es_rnsrs = []
    for rnsr in rnsrs:
        rnsr_id = rnsr['id']
        es_rnsr = {'id': rnsr['rnsr']}  # the 'id' field can be different from the rnsr, in some cases
        # CODE_NUMBERS
        code_numbers = []
        for code in [e['id'] for e in rnsr.get('externalIds', []) if e['type'] == 'label_numero']:
            code_numbers.extend([code, code.replace(' ', ''), code.replace(' ', '-'), code.replace(' ', '_')])
        es_rnsr['code_number'] = list(set(code_numbers))
        # ACRONYMS & NAMES
        es_rnsr['acronym'] = name_acronym_city[rnsr_id]['acronym']
        names = name_acronym_city[rnsr_id]['name']
        es_rnsr['name'] = list(set(names) - set(es_rnsr['acronym']) - set(es_rnsr['code_number']))
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
        es_rnsr['urban_unit'] = []
        for uu in name_acronym_city[rnsr_id]['urban_unit']:
            es_rnsr['urban_unit'] += urban_unit_composition[uu]
        es_rnsr['urban_unit'] = list(set(es_rnsr['urban_unit']))
        es_rnsr['country_alpha2'] = name_acronym_city[rnsr_id]['country_alpha2']
        es_rnsr['country_code'] = [name_acronym_city[rnsr_id]['country_alpha2']]
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
