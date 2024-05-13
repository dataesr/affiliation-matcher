import json
import os
import requests
import shutil

from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.config import CHUNK_SIZE, ROR_DUMP_URL
from project.server.main.elastic_utils import get_analyzers, get_tokenizers, get_char_filters, get_filters, get_index_name, get_mappings, get_mappings_direct
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import (
    insee_zone_emploi_data,
    geonames_french_departments,
    clean_list,
    clean_url,
    get_url_domain,
    normalize_text,
    ENGLISH_STOP,
    FRENCH_STOP,
    ACRONYM_IGNORED,
    GEO_IGNORED,
    COUNTRY_SWITCHER,
    CITY_COUNTRY,
)

logger = get_logger(__name__)

SOURCE = 'ror'
SCHEMA_VERSION = "2.0"
USE_ZONE_EMPLOI_COMPOSITION = False

def download_data() -> list:
    logger.debug(f'download ROR from {ROR_DUMP_URL}')
    ror_downloaded_file = 'ror_data_dump.zip'
    ror_unzipped_folder = mkdtemp()
    response = requests.get(url=ROR_DUMP_URL, stream=True)

    with open(file=ror_downloaded_file, mode='wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(file=ror_downloaded_file, mode='r') as file:
        file.extractall(ror_unzipped_folder)

    found_version = False
    for data_file in os.listdir(ror_unzipped_folder):
        if data_file.endswith('.json'):
            with open(f'{ror_unzipped_folder}/{data_file}', 'r') as file:
                data = json.load(file)
                # Check schema version
                if SCHEMA_VERSION == data[0].get("admin", {}).get("last_modified", {}).get("schema_version"):
                    found_version = True
                    break

    os.remove(path=ror_downloaded_file)
    shutil.rmtree(path=ror_unzipped_folder)

    if not found_version:
        logger.debug(f"Error: ROR schema version {SCHEMA_VERSION} not found in {ROR_DUMP_URL}")
        data = []

    return data


def transform_data(rors: list) -> list:
    logger.debug('transform data')

    # adding zone emploi data for France ie Saint Martin d'hères <-> Grenoble
    # Loading zone emploi data
    insee_zone_emploi, insee_city_zone_emploi = insee_zone_emploi_data(use_city_key=True)
    geonames_departments = geonames_french_departments()
    logger.debug(f"Geonames_departments = {len(geonames_departments)}")

    data = []
    for ror in rors:
        current_id = ror.get('id').replace('https://ror.org/', '')
        current_data = {"id": current_id}

        cities, countries, country_codes, zone_emploi = [], [], [], []
        for location in ror.get("locations", []):
            geonames_id = str(location.get("geonames_id") or "")
            geonames_details = location.get("geonames_details", {})
            city = geonames_details.get("name")
            country = geonames_details.get("country_name")
            country_code = geonames_details.get("country_code")

            if city:
                if city.lower() in CITY_COUNTRY:
                    countries += CITY_COUNTRY[city.lower()]

                if geonames_id and geonames_id in geonames_departments:
                    department = geonames_departments[geonames_id]
                    city_key = department + "_" + normalize_text(city, remove_separator=False, to_lower=True)
                    if city_key in insee_city_zone_emploi:
                        zone_emploi_code = insee_city_zone_emploi[city_key]
                        if USE_ZONE_EMPLOI_COMPOSITION:
                            zone_emploi += insee_zone_emploi[zone_emploi_code]["composition"]
                        else:
                            zone_emploi.append(insee_zone_emploi[zone_emploi_code]["name"])
                    else:
                        logger.warn(f"{city_key} not found in insee_city_zone_emploi")
                else:
                    if country == "France":
                        logger.warn(f"{geonames_id} ({city}) not in geonames_departments")

            if country_code and country_code.lower() in COUNTRY_SWITCHER:
                countries += COUNTRY_SWITCHER[country_code.lower()]

            cities.append(city)
            countries.append(country)
            country_codes.append(country_code)

        acronyms = [name.get("value") for name in ror.get("names", []) if "acronym" in name.get("types", [])]
        names = [name.get("value") for name in ror.get("names", []) if "acronym" not in name.get("types", [])]
        names_to_add = []
        for n in names:
            if 'institut' in n.lower() and 'institute' not in n.lower():
                names_to_add.append(n.lower().replace('institut', 'institute'))
            if n[0:11].lower()=='university ':
                names_to_add.append(n[11:]+' university')
                names_to_add.append(n[11:])
            if n[-11:].lower()==' university':
                names_to_add.append('university '+n[:-11])
                names_to_add.append(n[:-11])
        names += names_to_add

        grids, external_ids = [], {}
        for ext_ids in ror.get("external_ids"):
            ids_type = ext_ids.get("type")
            ids_values = ext_ids.get("all", [])
            if ids_type:
                if ids_type.lower() == "grid":
                    grids += ids_values
                else:
                    external_ids.setdefault(ids_type.lower() + "s", ids_values)

        supervisor_name = []
        for relation in ror.get("relationships", []):
            if relation.get("type") == "parent" and relation.get("label"):
                supervisor_name.append(relation.get("label"))

        urls, domains = [], []
        for link in ror.get("links", []):
            url = link.get("value")
            if url:
                urls.append(clean_url(url))
                urls.append(clean_url(url) + "/")
                domains.append(get_url_domain(url))

        current_data["acronym"] = clean_list(data=acronyms, ignored=ACRONYM_IGNORED, min_character=2)
        current_data["city"] = clean_list(data=cities, ignored=GEO_IGNORED)
        current_data["city_zone_emploi"] = clean_list(data=zone_emploi)
        current_data["country"] = clean_list(data=countries)
        current_data["country_code"] = clean_list(data=country_codes)
        current_data["name"] = clean_list(data=names, stopwords=FRENCH_STOP + ENGLISH_STOP, min_token=2)
        current_data["grid_id"] = clean_list(grids)
        current_data["external_ids"] = external_ids
        current_data["supervisor_name"] = clean_list(data=supervisor_name, stopwords=FRENCH_STOP + ENGLISH_STOP, min_token=2)
        current_data["web_url"] = clean_list(urls)
        current_data["web_domain"] = clean_list(domains)

        data.append(current_data)

    return data

def load_ror(index_prefix: str = 'matcher') -> dict:
    logger.debug('load ROR start')
    raw_data = download_data()
    transformed_data = transform_data(raw_data)
    # Init ES
    es_data = {}
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
        'id': 'light',
        'grid_id': 'light',
        'acronym': 'acronym_analyzer',
        'city': 'city_analyzer',
        'city_zone_emploi': 'city_analyzer',
        'city_nuts_level1': 'city_analyzer',
        'city_nuts_level2': 'city_analyzer',
        'city_nuts_level3': 'city_analyzer',
        'country': 'light',
        'country_code': 'light',
        'name': 'heavy_en',
        'supervisor_name': 'heavy_en',
        'web_url': 'url_analyzer',
        'web_domain': 'domain_analyzer'
    }
    exact_criteria = ['id', 'grid_id', 'acronym', 'city', 'country', 'country_code', 'supervisor_name', 'city_nuts_level1', 'city_nuts_level2', 'city_nuts_level3', 'city_zone_emploi', 'web_url', 'web_domain']
    txt_criteria = ['name']
    criteria = exact_criteria + txt_criteria
    criteria_unique = ['acronym', 'name']
    for c in criteria_unique:
        criteria.append(f'{c}_unique')
        analyzers[f'{c}_unique'] = analyzers[c]
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}
    external_ids_label = []
    # Iterate over ror data
    logger.debug('iterating over data points')
    for data_point in transformed_data:
        for criterion in criteria:
            criterion_values = data_point.get(criterion)
            if criterion_values is None:
                if 'city' not in criterion and 'unique' not in criterion:
                    logger.debug(f"This element {data_point['id']} has no {criterion}")
                continue
            if not isinstance(criterion_values, list):
                criterion_values = [criterion_values]
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                current_elt = { 
                    'id': data_point.get('id'),
                    'country_alpha2': data_point.get('country_code')
                }
                for ext_id in data_point.get('external_ids', {}):
                    current_elt[ext_id] = data_point['external_ids'][ext_id]
                    if ext_id not in external_ids_label:
                        external_ids_label.append(ext_id)
                es_data[criterion][criterion_value].append(current_elt)
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
        logger.debug(f'prep index {criterion}')
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            action = {
                '_index': index,
                'rors': [k['id'] for k in es_data[criterion][criterion_value]],
            }
            for other_id in ['country_alpha2', 'grids', 'rors', 'wikidatas']:
                all_codes = [k.get(other_id) for k in es_data[criterion][criterion_value] if other_id in k]
                codes = list(set([j for sub in all_codes for j in sub]))
                if codes:
                    action[other_id] = codes
            #if criterion in exact_criteria:
            #    action['query'] = {
            #        'match_phrase': {'content': {'query': criterion_value, 'analyzer': analyzer, 'slop': 1}}}
            #elif criterion in txt_criteria:
            #    action['query'] = {'match': {'content': {'query': criterion_value, 'analyzer': analyzer,
            #                                             'minimum_should_match': '-10%'}}}
            if criterion in criteria:
                action['query'] = {'match_phrase': {'content': {'query': criterion_value,
                                                                'analyzer': analyzer, 'slop': 0}}}
            actions.append(action)
    load_plain_simple_index = False
    if load_plain_simple_index:
        logger.debug('prep direct index')
        index = get_index_name(index_name='all', source=SOURCE, index_prefix=index_prefix, simple=True)
        es.create_index(index=index, mappings=get_mappings_direct(analyzers), settings=settings)
        results[index] = len(transformed_data)
        for current_data in transformed_data: 
            action = { '_index': index }
            action.update(current_data)
            actions.append(action)
    logger.debug('bulk insert')
    es.parallel_bulk(actions=actions)
    return results
