import os
import datetime
import pandas as pd
import requests
from elasticsearch.client import IndicesClient
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
    insee_zone_emploi_data,
    get_alpha2_from_french,
    FRENCH_STOP,
    clean_list,
    ACRONYM_IGNORED,
    clean_url,
    get_url_domain,
    clean_city,
    normalize_text,
)

logger = get_logger(__name__)

SOURCE = "paysage"
PAYSAGE_API_URL = "https://paysage-api.staging.dataesr.ovh"
PAYSAGE_API_KEY = os.getenv("PAYSAGE_API_KEY")
USE_ZONE_EMPLOI_COMPOSITION = False

CATEGORIES = {
    "mCpLW": "Université",
    "Eg7tX": "Établissement public expérimental",
    "93BR1": "Établissement supérieur d'architecture",
    "2ZdzP": "Organisme de recherche",
    "MTFHZ": "Société d'accélération du transfert de technologies",
    "UfEnK": "Établissement d'enseignement supérieur privé d'intérêt général",
    "Sv5bb": "Tutelle des établissements",
    "mNJ1Z": "Incubateur public",
    "WCat8": "Liste des établissements publics relevant du ministre chargé de l'Enseignement supérieur",
    "fQ6GL": "Etablissements d’enseignement supérieur techniques privés (hors formations relevant du commerce et de la gestion)",
    "WkSgR": "Etablissement publics d’enseignement supérieur entrant dans la cotutelle du ministre chargé de l’enseignement supérieur (Art L 123-1 du code de l’éducation)",
    "YNqFb": "Commerce et gestion - Etablissements d’enseignement supérieur techniques privés et consulaires autorisés à délivrer un diplôme visé par le ministre chargé de l’enseignement supérieur et/ou à conférer le grade universitaire",
    "iyn79": "Opérateur du programme 150 - Formations supérieures et recherche universitaire",
    "z367d": "Structure de recherche",
    "NsMkU": "Établissement d'enseignement supérieur étranger",
}


def load_paysage(index_prefix: str = "matcher") -> dict:
    """Load paysage data ton elastic indexes"""

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
        "acronym",
        "name",
        "year",
        "country",
        "country_alpha2",
        "country_alpha3",
        "web_url",
        "web_domain",
    ]
    txt_criteria = ["name_txt"]
    analyzers = {
        "id": "light",
        "city": "city_analyzer",
        "zone_emploi": "city_analyzer",
        "acronym": "acronym_analyzer",
        "name": "heavy_fr",
        "name_txt": "heavy_fr",
        "year": "light",
        "country": "light",
        "country_alpha2": "light",
        "country_alpha3": "light",
        "web_url": "url_analyzer",
        "web_domain": "domain_analyzer",
    }
    criteria = exact_criteria + txt_criteria
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
    if not raw_data:
        logger.error("Loading aborted: no paysage data")
        return {}

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
                es_data[criterion][criterion_value].append({"id": data_point["id"]})

    # Bulk insert data into ES
    actions = []
    results = {}
    for criterion in list(es_data.keys()):
        index = get_index_name(index_name=criterion, source=SOURCE, index_prefix=index_prefix)
        analyzer = analyzers[criterion]
        results[index] = len(es_data[criterion])
        for criterion_value in es_data[criterion]:
            action = {
                "_index": index,
                "paysages": [k["id"] for k in es_data[criterion][criterion_value]],
            }
            if criterion in exact_criteria:
                action["query"] = {
                    "match_phrase": {
                        "content": {
                            "query": criterion_value,
                            "analyzer": analyzer,
                            "slop": 1,
                        }
                    }
                }
            elif criterion in txt_criteria:
                action["query"] = {
                    "match": {
                        "content": {
                            "query": criterion_value,
                            "analyzer": analyzer,
                            "minimum_should_match": "-10%",
                        }
                    }
                }
            actions.append(action)
    logger.debug("Start load elastic indexes")
    es.parallel_bulk(actions=actions)
    return results


def download_data() -> list:
    """Request paysage data from api"""
    logger.debug("Start requesting paysage api")

    if not PAYSAGE_API_KEY:
        logger.error(f"Error: no paysage-api key found")
        return None

    # Request data
    limit = 10000
    headers = {"X-API-KEY": PAYSAGE_API_KEY}
    data = []

    for category in CATEGORIES:
        url = f"{PAYSAGE_API_URL}/relations?limit={limit}&filters[relationTag]=structure-categorie&filters[relatedObjectId]={category}"
        response = requests.get(url=url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error {response.status_code} requesting {url}")
            continue

        current_data = response.json().get("data")
        # logger.debug(f"Found {len(current_data)} paysage records for category {CATEGORIES[category]}")

        current_data = pd.DataFrame(current_data).drop_duplicates(subset="resourceId").to_dict(orient="records")
        logger.debug(f"Found {len(current_data)} paysage records for category {CATEGORIES[category]} without duplicates")

        data += current_data

    df = pd.DataFrame(data)
    data = (
        df.groupby(by="resourceId")
        .agg({k: list if k == "relatedObjectId" else "first" for k in df.columns})
        .to_dict(orient="records")
    )
    logger.debug(f"Keep {len(data)} paysage records without duplicates")

    return data


def transform_data(data: list) -> list:
    """Transform paysage data to elastic data"""

    logger.debug(f"Start transform of Paysage data ({len(data)} records)")
    es_records = []

    # Loading zone emploi data
    insee_zone_emploi, insee_city_zone_emploi = insee_zone_emploi_data(use_city_key=True)

    # Setting a dict with all names, acronyms and cities
    logger.debug("Get data from Paysage records")
    for record in data:
        current_id = record["resourceId"]
        es_record = {"id": current_id}

        resource = record["resource"]
        naming = resource.get("currentName", {})
        localisation = resource.get("currentLocalisation", {})

        # Acronyms
        acronyms_list = ["acronymFr", "acronymEn", "acronymLocal"]
        acronyms = [naming.get(acronym) for acronym in acronyms_list if naming.get(acronym)]

        # Names
        names_list = ["usualName", "officialName", "nameEn"]
        names = [naming.get(name) for name in names_list if naming.get(name)]

        short_name = naming.get("shortName")
        if short_name:
            if short_name.isalnum():
                acronyms.append(short_name)
            else:
                names.append(short_name)

        acronyms = list(set(acronyms))
        names = list(set(names))
        names = list(set(names) - set(acronyms))

        # City
        raw_city = localisation.get("locality")
        city = clean_city(raw_city) or raw_city

        # Zone emploi
        zone_emploi = []
        zone_emploi_code = None
        city_code = localisation.get("postalCode")
        if city and city_code:
            norm_city = normalize_text(city, remove_separator=False, to_lower=True)
            city_dep = city_code[:3] if city_code.startswith("97") else city_code[:2]
            city_key = city_dep + "_" + norm_city
            if city_key in insee_city_zone_emploi:
                zone_emploi_code = insee_city_zone_emploi[city_key]
            else:
                if localisation.get("country") == "France":
                    logger.warn(f"{city_key} ({raw_city}) not found in insee_city_zone_emploi")
        if zone_emploi_code:
            if USE_ZONE_EMPLOI_COMPOSITION:
                zone_emploi += insee_zone_emploi[zone_emploi_code]["composition"]
            else:
                zone_emploi.append(insee_zone_emploi[zone_emploi_code]["name"])

        # Countries
        country = localisation.get("country")
        country_alpha2 = get_alpha2_from_french(country) if country else None
        country_alpha3 = localisation.get("iso3")

        # Dates
        start_date = resource.get("creationDate")
        if not start_date:
            start_date = "2010"
        start = int(start_date[0:4])
        end_date = resource.get("closureDate")
        if not end_date:
            end_date = f"{datetime.date.today().year}"
        end = int(end_date[0:4])
        # Start date one year before official as it can be used before sometimes
        years = [str(y) for y in list(range(start - 1, end + 1))]

        # Websites
        web_urls, web_domains = [], []
        websites = resource.get("websites", [])
        for website in websites:
            url = website.get("url")
            if url:
                web_urls.append(clean_url(url))
                web_domains.append(get_url_domain(url))
        web_urls = list(set(web_urls))
        web_domains = list(set(web_domains))

        # Elastic record
        es_record["acronym"] = clean_list(
            data=acronyms,
            stopwords=FRENCH_STOP,
            ignored=ACRONYM_IGNORED,
            min_character=2,
        )
        es_record["name"] = clean_list(data=names, stopwords=FRENCH_STOP, min_token=2)
        es_record["city"] = clean_list(data=city, stopwords=FRENCH_STOP, min_character=2)
        es_record["zone_emploi"] = clean_list(data=zone_emploi, stopwords=FRENCH_STOP)
        es_record["country"] = clean_list(data=country, stopwords=FRENCH_STOP)
        es_record["country_alpha2"] = clean_list(data=country_alpha2, stopwords=FRENCH_STOP)
        es_record["country_alpha3"] = clean_list(data=country_alpha3, stopwords=FRENCH_STOP)
        es_record["year"] = years
        es_record["web_url"] = web_urls
        es_record["web_domain"] = web_domains

        es_records.append(es_record)

    return es_records
