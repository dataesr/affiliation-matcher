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

logger = get_logger(__name__)
SOURCE = 'ror'


def download_ror_data() -> list:
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


def clean(data: list) -> list:
    # Cast data into list if needed
    if not isinstance(data, list):
        data = [data]
    # Remove duplicates
    data = list(set(data))
    # Remove None values
    data = list(filter(None, data))
    return data

def get_external_ids(external):
    ids = []
    for k in external:
        if isinstance(external[k], list):
            ids += external[k]
        elif isinstance(external[k], str):
            ids.append(external[k])
    return list(set(ids))

def transform_ror_data(rors: list) -> list:
    data = []
    for ror in rors:
        acronym = ror.get('acronyms', [])
        city = [address.get('city') for address in ror.get('addresses', [])]
        country = [ror.get('country', {}).get('country_name')]
        country_code = [ror.get('country', {}).get('country_code').lower()]
        id = ror.get('id').replace('https://ror.org/', '')
        name = [ror.get('name')]
        name += ror.get('aliases', [])
        name += [label.get('label') for label in ror.get('labels', [])]
        externals = ror.get('external_ids', [])
        external_ids = {}
        for ext_id in list(externals.keys()):
            external_ids[ext_id.lower()+'s'] = get_external_ids(externals[ext_id])
        data.append({
            'acronym': clean(data=acronym),
            'city': clean(data=city),
            'country': clean(data=country),
            'country_code': clean(data=country_code),
            'id': id,
            'name': clean(data=name),
        })
    return data


def load_ror(index_prefix: str = 'matcher') -> dict:
    rors = download_ror_data()
    rors = transform_ror_data(rors=rors)
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
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'name': 'heavy_en'
    }
    criteria = ['acronym', 'city', 'country', 'country_code', 'name']
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    external_ids_label = []
    # Iterate over ror data
    for ror in rors:
        for criterion in criteria:
            criterion_values = ror.get(criterion)
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                current_elt = { 
                    'id': ror.get('id'),
                    'country_code': ror.get('country_code')
                }
                for ext_id in ror.get('external_ids', {}):
                    current_elt[ext_id] = ror['external_ids'][ext_id]
                    if ext_id not in external_ids_label:
                        external_ids_label.append(ext_id)
                es_data[criterion][criterion_value].append(current_elt)
    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in es_data:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            country_codes = [k.get('country_code', '') for k in es_data[criterion][criterion_value]]
            action = {
                '_index': index,
                'rors': [k['id'] for k in es_data[criterion][criterion_value]],
                'country_alpha2': list(set([j for sub in country_codes for j in sub]))
            }
            for ext_id in external_ids_label:
                action[ext_id] = list(set([k[ext_id] for k in es_data[criterion][criterion_value]]))
            if criterion in criteria:
                action['query'] = {'match_phrase': {'content': {'query': criterion_value,
                                                                'analyzer': analyzer, 'slop': 0}}}
            actions.append(action)
    es.parallel_bulk(actions=actions)
    return results
