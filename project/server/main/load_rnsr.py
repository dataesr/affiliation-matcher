import datetime
import requests
import pandas as pd
import numpy as np
from elasticsearch.client import IndicesClient

from project.server.main.config import SCANR_DUMP_URL
from project.server.main.elastic_utils import get_analyzers, get_tokenizers, get_char_filters, get_filters, get_index_name, get_mappings
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import (
    insee_zone_emploi_data,
    get_alpha2_from_french,
    FRENCH_STOP,
    clean_list,
    ACRONYM_IGNORED,
    clean_url,
    get_url_domain,
)

logger = get_logger(__name__)

SOURCE = 'rnsr'
USE_ZONE_EMPLOI_COMPOSITION = False


def download_data() -> list:
    logger.debug(f"download RNSR data from {SCANR_DUMP_URL}")
    if "jsonl" in SCANR_DUMP_URL:
        data = pd.read_json(SCANR_DUMP_URL, lines=True).replace(np.nan, None).to_dict(orient="records")
    else:
        r = requests.get(SCANR_DUMP_URL)
        data = r.json()
    return data


RNSR_DATA = download_data()

def load_rnsr(index_prefix: str = 'matcher') -> dict:
    logger.debug('load rnsr ...')
    es = MyElastic()
    indices_client = IndicesClient(es)
    settings = {
        'analysis': {
            'analyzer': get_analyzers(),
            'tokenizer': get_tokenizers(),
            'char_filter': get_char_filters(),
            'filter': get_filters()
        }
    }
    exact_criteria = ['id', 'city', 'urban_unit', 'zone_emploi', 'country_code', 'acronym', 'code_number', 'code_prefix',
                      'supervisor_acronym', 'year', 'name', 'supervisor_name', 'web_url', 'web_domain']
    txt_criteria = ['name_txt']
    analyzers = {
        'id': 'light',
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'urban_unit': 'city_analyzer',
        'zone_emploi': 'city_analyzer',
        'country_code': 'light',
        'code_prefix': 'light',
        'code_number': 'code_analyzer',
        'name': 'heavy_fr',
        'name_txt': 'heavy_fr',
        'supervisor_acronym': 'acronym_analyzer',
        'supervisor_name': 'heavy_fr',
        'year': 'light',
        'web_url': 'url_analyzer',
        'web_domain': 'domain_analyzer'
    }
    criteria = exact_criteria + txt_criteria
    criteria_unique = []
    for c in criteria_unique:
        criteria.append(f'{c}_unique')
        analyzers[f'{c}_unique'] = analyzers[c]
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    raw_data = RNSR_DATA
    transformed_data = transform_data(raw_data)
    logger.debug('prepare data for ES')
    # Iterate over rnsr data
    for data_point in transformed_data:
        for criterion in criteria:
            criterion_values = data_point.get(criterion.replace('_txt', ''))
            if criterion_values is None:
                # logger.debug(f'This element {data_point} has no {criterion}')
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
            # if criterion in ['name']:
            #    tokens = get_tokens(indices_client, analyzer, index, criterion_value)
            #    if len(tokens) < 2:
            #        logger.debug(f'Not indexing {criterion_value} (not enough token to be relevant !)')
            #        continue
            action = {'_index': index, 'rnsrs': [k['id'] for k in es_data[criterion][criterion_value]],
                      'country_alpha2': list(set([k['country_alpha2'] for k in es_data[criterion][criterion_value]]))}
            if criterion in exact_criteria:
                action['query'] = {
                    'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 1}}}
            elif criterion in txt_criteria:
                action['query'] = {'match': {'content': {'query': criterion_value, 'analyzer': analyzer,
                                                         'minimum_should_match': '-10%'}}}
            actions.append(action)
    logger.debug('load ES')
    es.parallel_bulk(actions=actions)
    return results


def get_values(x: dict) -> list:
    if x.get('fr', '') == x.get('en', '') and x.get('fr'):
        return [x['fr']]
    if (x.get('en', '') in x.get('default', '')) and (x.get('fr', '') in x.get('default', '')) and 'default' in x:
        del x['default']
    return list(set(x.values()))


def get_siren():
    correspondance = {}
    raw_rnsrs = RNSR_DATA
    for r in raw_rnsrs:
        current_id = None
        for e in r.get('externalIds', []):
            if e['type'] in ['rnsr', 'grid']:
                current_id = e['id']
                if current_id not in correspondance:
                    correspondance[current_id] = []
        if current_id is None:
            continue

        for e in r.get('externalIds', []):
            if e not in correspondance[current_id] and e['type'] in ['siren', 'siret', 'sirene']:
                correspondance[current_id].append(e)

        for e in r.get('institutions'):
            if e.get('structure'):
                if isinstance(e.get('relationType'), str) and 'tutelle' in e['relationType'].lower():
                    elt = {'id': e['structure'], 'type': 'siren'}
                    if elt not in correspondance[current_id]:
                        correspondance[current_id].append(elt)
    logger.debug(f'{len(correspondance)} ids loaded with equivalent ids')
    return correspondance

def transform_data(data: list) -> list:
    logger.debug('transform RNSR data')
    rnsrs = []
    for d in data:
        external_ids = d.get('externalIds', [])
        if 'rnsr' in [e['type'] for e in external_ids]:
            d['rnsr'] = [e['id'] for e in external_ids if e['type'] == 'rnsr'][0]
            rnsrs.append(d)
    logger.debug(f'{len(rnsrs)} rnsr elements detected in dump')

    # Loading zone emploi data
    # Loading zone emploi data
    insee_zone_emploi, insee_city_zone_emploi = insee_zone_emploi_data()

    # Setting a dict with all names, acronyms and cities
    name_acronym_city = {}
    urban_unit_composition = {}
    for d in data:
        current_id = d['id']
        name_acronym_city[current_id] = {}
        # Acronyms
        acronyms = []
        if d.get('acronym'):
            acronyms = get_values(d.get('acronym', []))
        # Names
        names = []
        if d.get('label'):
            names += get_values(d.get('label', []))
        if d.get('alias'):
            names += d.get('alias')
        for n in names:
            if n.lower()[0:18] in ['unité de recherche', 'unite de recherche']:
                names.append(n[18:].strip())
        names = list(set(names))
        names = list(set(names) - set(acronyms))
        # Cities, country_alpha2, urban_units and zone_emploi
        cities, country_alpha2, urban_units, zone_emploi = [], [], [], []
        for address in d.get('address', []):
            if 'city' in address and address['city']:
                cities.append(address['city'])
            if 'city' in address and address['city'] and 'citycode' in address and address['citycode']:
                city_code = address['citycode']
                if city_code and city_code in insee_city_zone_emploi:
                    zone_emploi.append(insee_city_zone_emploi[city_code])
            if 'urbanUnitLabel' in address and address['urbanUnitLabel']:
                urban_units.append(address['urbanUnitLabel'])
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
        name_acronym_city[current_id]['city'] = clean_list(data = cities)
        name_acronym_city[current_id]['zone_emploi'] = clean_list(data = zone_emploi)
        name_acronym_city[current_id]['urban_unit'] = clean_list(data = urban_units)
        name_acronym_city[current_id]['acronym'] = clean_list(data = acronyms, ignored=ACRONYM_IGNORED, min_character = 2)
        name_acronym_city[current_id]['name'] = clean_list(data = names, stopwords = FRENCH_STOP, min_token = 2)
        country_alpha2 = clean_list(data = country_alpha2)
        if not country_alpha2:
            country_alpha2 = ['fr']
        name_acronym_city[current_id]['country_alpha2'] = country_alpha2[0]
    es_rnsrs = []
    for rnsr in rnsrs:
        rnsr_id = rnsr['id']
        es_rnsr = {'id': rnsr['rnsr']}  # the 'id' field can be different from the rnsr, in some cases
        # Code numbers
        code_numbers = []
        code_prefixes = []
        for code in [e['id'] for e in rnsr.get('externalIds', []) if e['type'] == 'label_numero']:
            code_numbers.extend([code, code.replace(' ', ''), code.replace(' ', '-'), code.replace(' ', '_')])
            code_prefix = code.split(' ')[0]
            if len(code_prefix)>=3:
                for subp in ['umr', 'umi', 'ums', 'gdr', 'cic']:
                    if subp in code_prefix.lower():
                        code_prefixes.append(code_prefix)
        es_rnsr['code_number'] = list(set(code_numbers))
        es_rnsr['code_prefix'] = list(set(code_prefixes))
        # Acronyms & names
        es_rnsr['acronym'] = name_acronym_city[rnsr_id]['acronym']
        names = name_acronym_city[rnsr_id]['name']
        es_rnsr['name'] = list(set(names) - set(es_rnsr['acronym']) - set(es_rnsr['code_number']))
        # Supervisors id
        es_rnsr['supervisor_id'] = [supervisor.get('structure') for supervisor in rnsr.get('institutions', [])
                                    if 'structure' in supervisor]
        es_rnsr['supervisor_id'] += [external_id['id'][0:9] for external_id in rnsr.get('externalIds', [])
                                     if external_id['type'] and 'sire' in external_id['type']]
        es_rnsr['supervisor_id'] = clean_list(data = es_rnsr['supervisor_id'])
        # Supervisors acronym, name and city
        for f in ['acronym', 'name', 'city']:
            es_rnsr[f'supervisor_{f}'] = []
            for supervisor_id in es_rnsr['supervisor_id']:
                if supervisor_id in name_acronym_city:
                    es_rnsr[f'supervisor_{f}'] += name_acronym_city[supervisor_id][f'{f}']
            es_rnsr[f'supervisor_{f}'] = clean_list(es_rnsr[f'supervisor_{f}'])
        # Addresses
        es_rnsr['city'] = name_acronym_city[rnsr_id]['city']
        es_rnsr['country_alpha2'] = name_acronym_city[rnsr_id]['country_alpha2']
        es_rnsr['country_code'] = [name_acronym_city[rnsr_id]['country_alpha2']]
        # for urban units and zone emploi, all the cities around are added, so that, eg, Bordeaux is in
        # zone_emploi of a lab located in Talence
        es_rnsr['urban_unit'] = []
        for uu in name_acronym_city[rnsr_id]['urban_unit']:
            es_rnsr['urban_unit'] += urban_unit_composition[uu]
        es_rnsr['urban_unit'] = list(set(es_rnsr['urban_unit']))
        # Now zone emploi (larger than urban unit)
        es_rnsr["zone_emploi"] = []
        for ze in name_acronym_city[rnsr_id]["zone_emploi"]:
            if USE_ZONE_EMPLOI_COMPOSITION:
                es_rnsr["zone_emploi"] += insee_zone_emploi[ze]["composition"]
            else:
                es_rnsr["zone_emploi"].append(insee_zone_emploi[ze]["name"])
        es_rnsr['zone_emploi'] = clean_list(es_rnsr['zone_emploi'])
        # Dates
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

        urls, domains = [], []
        if isinstance(rnsr.get('links'), list):
            for link in rnsr['links']:
                current_link = link.get('url')
                if current_link and link.get('type') == 'main':
                    urls.append(clean_url(current_link))
                    urls.append(clean_url(current_link)+'/')
                    domains.append(get_url_domain(current_link))
        if urls:
            es_rnsr['web_url'] = urls
        if domains:
            es_rnsr['web_domain'] = domains

        es_rnsrs.append(es_rnsr)
    return es_rnsrs
