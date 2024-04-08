import os
import datetime
import pandas as pd
import numpy as np
from elasticsearch.client import IndicesClient

ODS_KEY = os.getenv("ODS_KEY")
ODS_PAYSAGE = "fr_esr_paysage_structures_all"

from project.server.main.elastic_utils import (
    get_analyzers,
    get_tokenizers,
    get_char_filters,
    get_filters,
    get_index_name,
    get_mappings,
)
from project.server.main.logger import get_logger
from project.server.main.my_elastic import MyElastic
from project.server.main.utils import (
    download_insee_data,
    get_alpha2_from_french,
    FRENCH_STOP,
    clean_list,
    ACRONYM_IGNORED,
    clean_url,
    get_url_domain,
)

logger = get_logger(__name__)

SOURCE = "paysage"


def load_paysage(index_prefix: str = "matcher") -> dict:
    logger.debug("Start loading Paysage data...")
    es = MyElastic()
    indices_client = IndicesClient(es)
    settings = {
        "analysis": {
            "analyzer": get_analyzers(),
            "tokenizer": get_tokenizers(),
            "char_filter": get_char_filters(),
            "filter": get_filters(),
        }
    }
    exact_criteria = [
        "id",
        "city",
        "zone_emploi",
        "country_code",
        "acronym",
        "year",
        "name",
        "year",
        "wikidata",
        "web_url",
        "web_domain",
    ]
    txt_criteria = ["name_txt"]
    analyzers = {
        "id": "light",
        "city": "city_analyzer",
        "zone_emploi": "city_analyzer",
        "country_code": "light",
        "acronym": "acronym_analyzer",
        "name": "heavy_fr",
        "name_txt": "heavy_fr",
        "wikidata": "wikidata_analyzer",
        "year": "light",
        "web_url": "url_analyzer",
        "web_domain": "domain_analyzer",
    }
    criteria = exact_criteria + txt_criteria
    criteria_unique = []
    for c in criteria_unique:
        criteria.append(f"{c}_unique")
        analyzers[f"{c}_unique"] = analyzers[c]

    logger.debug(f"Criteria {criteria}")

    # Create Elastic Search index
    es_data = {}
    for criterion in criteria:
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        es.create_index(index=index, mappings=get_mappings(analyzer), settings=settings)
        es_data[criterion] = {}

    # Download paysage data
    raw_data = download_data()

    # Transform paysage data
    transformed_data = transform_data(raw_data)

    # Iterate over paysage data
    logger.debug("Prepare data for elastic")
    for data_point in transformed_data:
        for criterion in criteria:
            criterion_values = data_point.get(criterion.replace("_txt", ""))
            if criterion_values is None:
                # logger.debug(f'This element {data_point} has no {criterion}')
                continue
            if not isinstance(criterion_values, list):
                criterion_values = [criterion_values]
            for criterion_value in criterion_values:
                if criterion_value not in es_data[criterion]:
                    es_data[criterion][criterion_value] = []
                es_data[criterion][criterion_value].append(
                    {"id": data_point["id"], "country_alpha2": data_point["country_alpha2"]}
                )
    # Add unique criterion
    for criterion in criteria_unique:
        for criterion_value in es_data[criterion]:
            if len(es_data[criterion][criterion_value]) == 1:
                if f"{criterion}_unique" not in es_data:
                    es_data[f"{criterion}_unique"] = {}
                es_data[f"{criterion}_unique"][criterion_value] = es_data[criterion][criterion_value]

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
            action = {
                "_index": index,
                "paysages": [k["id"] for k in es_data[criterion][criterion_value]],
                "country_alpha2": list(set([k["country_alpha2"] for k in es_data[criterion][criterion_value]])),
            }
            if criterion in exact_criteria:
                action["query"] = {
                    "match_phrase": {"content": {"query": criterion_value, "analyzer": analyzer, "slop": 1}}
                }
            elif criterion in txt_criteria:
                action["query"] = {
                    "match": {
                        "content": {"query": criterion_value, "analyzer": analyzer, "minimum_should_match": "-10%"}
                    }
                }
            actions.append(action)
    logger.debug("Start load elastic indexes")
    es.parallel_bulk(actions=actions)
    return results


def download_data() -> list:
    logger.debug(f"Download Paysage data from {ODS_PAYSAGE}")
    data = (
        pd.read_csv(
            f"https://data.enseignementsup-recherche.gouv.fr/explore/dataset/{ODS_PAYSAGE}/download/?format=csv&apikey={ODS_KEY}",
            sep=";",
            low_memory=False,
        )
        .replace(np.nan, None)
        .to_dict(orient="records")
    )
    return data


def transform_data(data: list) -> list:
    logger.debug(f"Start transform of Paysage data ({len(data)} records)")

    # Loading zone emploi data
    logger.debug(f"Download insee data")
    zone_emploi_insee = download_insee_data()
    zone_emploi_composition = {}
    city_zone_emploi = {}
    for d in zone_emploi_insee:
        city = d["LIBGEO"]
        city_code = d["CODGEO"]
        ze = d["LIBZE2020"]
        if ze not in zone_emploi_composition:
            zone_emploi_composition[ze] = []
        zone_emploi_composition[ze].append(city)
        if city_code not in city_zone_emploi:
            city_zone_emploi[city_code] = []
        city_zone_emploi[city_code].append(ze)

    # Setting a dict with all names, acronyms and cities
    logger.debug("Get data from Paysage records")
    name_acronym_city = {}
    for d in data:
        current_id = d["identifiant_interne"]
        name_acronym_city[current_id] = {}
        # Acronyms
        acronyms = [d.get("sigle")] if d.get("sigle") else []
        # Names
        labels = ["uo_lib", "uo_lib_officiel", "uo_lib_en", "nom_court"]
        names = [d.get(name) for name in labels if d.get(name)]
        names = list(set(names))
        names = list(set(names) - set(acronyms))
        # Cities, country_alpha2, and zone_emploi
        cities, country_alpha2, zone_emploi = [], [], []
        city = d.get("com_nom")
        city_code = d.get("com_code")
        country = d.get("pays_etranger_acheminement")
        if city:
            cities.append(city)
            if city_code in city_zone_emploi:
                zone_emploi += city_zone_emploi[city_code]
        if country:
            alpha2 = get_alpha2_from_french(country)
            country_alpha2.append(alpha2)

        name_acronym_city[current_id]["city"] = clean_list(data=cities)
        name_acronym_city[current_id]["zone_emploi"] = clean_list(data=zone_emploi)
        name_acronym_city[current_id]["acronym"] = clean_list(data=acronyms, ignored=ACRONYM_IGNORED, min_character=2)
        name_acronym_city[current_id]["name"] = clean_list(data=names, stopwords=FRENCH_STOP, min_token=2)
        country_alpha2 = clean_list(data=country_alpha2)
        if not country_alpha2:
            country_alpha2 = ["fr"]
        name_acronym_city[current_id]["country_alpha2"] = country_alpha2[0]

    logger.debug("Transform records to elastic indexes")
    es_paysages = []
    for d in data:
        paysage_id = d.get("identifiant_interne")
        es_paysage = {"id": paysage_id}
        # Acronyms & names
        es_paysage["acronym"] = name_acronym_city[paysage_id]["acronym"]
        names = name_acronym_city[paysage_id]["name"]
        es_paysage["name"] = list(set(names) - set(es_paysage["acronym"]))
        # Addresses
        es_paysage["city"] = name_acronym_city[paysage_id]["city"]
        es_paysage["country_alpha2"] = name_acronym_city[paysage_id]["country_alpha2"]
        es_paysage["country_code"] = [name_acronym_city[paysage_id]["country_alpha2"]]
        # For zone emploi, all the cities around are added, so that, eg, Bordeaux is in
        # zone_emploi of a lab located in Talence
        es_paysage["zone_emploi"] = []
        for ze in name_acronym_city[paysage_id]["zone_emploi"]:
            es_paysage["zone_emploi"] += zone_emploi_composition[ze]
        es_paysage["zone_emploi"] = clean_list(es_paysage["zone_emploi"])
        # Wikidata
        wikidata = d.get("identifiant_wikidata")
        if wikidata:
            es_paysage["wikidata"] = wikidata
        # Dates
        last_year = f"{datetime.date.today().year}"
        start_date = d.get("date_creation")
        if not start_date:
            start_date = "2010"
        start = int(start_date[0:4])
        end_date = d.get("date_fermeture")
        if not end_date:
            end_date = last_year
        end = int(end_date[0:4])
        # Start date one year before official as it can be used before sometimes
        es_paysage["year"] = [str(y) for y in list(range(start - 1, end + 1))]
        # Url
        url = d.get("url")
        if isinstance(url, list):
            raise Exception("found list url", url)
        if url:
            es_paysage["web_url"] = clean_url(url)
            es_paysage["web_domain"] = get_url_domain(url)

        es_paysages.append(es_paysage)
    return es_paysages
