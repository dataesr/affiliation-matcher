import os
import sys
import requests
import pandas as pd
import numpy as np
from enum import Enum
from tenacity import retry, wait_fixed
from dotenv import load_dotenv

load_dotenv()

PAYSAGE_API_URL = "https://paysage-api.staging.dataesr.ovh"
PAYSAGE_API_KEY = os.getenv("PAYSAGE_API_KEY")

AFFILIATION_MATCHER_API = f"{os.getenv('AFFILIATION_MATCHER_URL')}/match"
AFFILIATION_MATCHER_LIST_API = "http://localhost:5004/match_list"
AFFILIATION_MATCHER_LIST_TASK_API = "http://localhost:5004/tasks"

MATCH_TYPE = "rnsr"
COL_RNSR_ID = "identifiant_rnsr"
COL_PAYSAGE_ID = "identifiant_interne"
COL_MATCH_ID = COL_RNSR_ID
COL_ACRONYM = "sigle"
COL_NAME = "name"
COL_ADDRESS = "address"
COL_CITY = "city"
COL_COUNTRY = "pays_etranger_acheminement"
COL_YEAR = "date_fermeture"
SUBSET_ADDRESS = [COL_ADDRESS, COL_CITY, COL_COUNTRY]

COL_AFFILIATION_STR = "affiliation_string"
COL_AFFILIATION_MATCH = "affiliation_match"
COL_AFFILIATION_IS_MATCH = "affiliation_is_match"

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
    # "NsMkU": "Établissement d'enseignement supérieur étranger",
}

class MATCH(Enum):
    NO_ID_NO_MATCH = 0
    ID_NO_MATCH = 1
    ID_MATCH = 2
    ID_DIFF_MATCH = 3
    NO_ID_MATCH = 6


def paysage_get_data() -> list:
    """Request paysage data from api"""
    print("Start requesting paysage api")

    # Request data
    limit = 10000
    filters = "&".join([f"filters[relatedObjectId]={category}" for category in list(CATEGORIES.keys())])
    url = f"{PAYSAGE_API_URL}/relations?limit={limit}&filters[relationTag]=structure-categorie&{filters}"
    headers = {"X-API-KEY": PAYSAGE_API_KEY}
    response = requests.get(url=url, headers=headers)

    if response.status_code != 200:
        print(f"Error {response.status_code} requesting {url}")
        return None

    data = response.json().get("data")
    # print(f"Found {len(data)} paysage records for {len(CATEGORIES)} categories")

    data = pd.DataFrame(data).drop_duplicates(subset="resourceId").to_dict(orient="records")
    # print(f"Keep {len(data)} paysage records without duplicates")

    return data


def paysage_transform_data(data):
    df_dict = {
        COL_PAYSAGE_ID: [],
        COL_RNSR_ID: [],
        COL_ACRONYM: [],
        COL_NAME: [],
        COL_ADDRESS: [],
        COL_CITY: [],
        COL_COUNTRY: [],
        COL_YEAR: [],
    }

    for record in data:
        id = record.get("resourceId")
        resource = record.get("resource")
        identifiers = resource.get("identifiers", [])
        naming = resource.get("currentName", {})
        localisation = resource.get("currentLocalisation", {})

        rnsr_id = [i.get("value") for i in identifiers if i.get("type") == "rnsr"]
        acronym = naming.get("acronymFr") or naming.get("acronymEn") or naming.get("acronymLocal")
        name = naming.get("usualName") or naming.get("officialName") or naming.get("nameEn") or naming.get("shortName")
        address = localisation.get("address")
        city = localisation.get("locality")
        country = localisation.get("country")
        year = resource.get("closureDate")[0:4] if resource.get("closureDate") else None

        df_dict[COL_PAYSAGE_ID].append(id)
        df_dict[COL_RNSR_ID].append(rnsr_id)
        df_dict[COL_ACRONYM].append(acronym)
        df_dict[COL_NAME].append(name)
        df_dict[COL_ADDRESS].append(address)
        df_dict[COL_CITY].append(city)
        df_dict[COL_COUNTRY].append(country)
        df_dict[COL_YEAR].append(year)

    return pd.DataFrame.from_dict(df_dict, orient="columns")


def paysage_get_name(paysage_row: pd.Series, use_acronym=False):
    name = paysage_row[COL_NAME]

    if use_acronym:
        acronym = paysage_row[COL_ACRONYM]
        name = f"{acronym} - {name}"

    return name


def paysage_get_address(paysage_row: pd.Series):
    adress = paysage_row[SUBSET_ADDRESS].dropna().to_list()
    adress_str = ", ".join(adress)
    return adress_str


def paysage_get_affiliations(paysage_row: pd.Series, use_acronym=False):
    name = paysage_get_name(paysage_row, use_acronym)
    adress = paysage_get_address(paysage_row)
    affiliations = f"{name}, {adress}"
    return affiliations


# api/match
def affiliation_get_matches(affiliation: str, year=None):
    if not affiliation:
        return []

    body = {"type": MATCH_TYPE, "query": affiliation}
    if year:
        body["year"] = year

    res = requests.post(url=AFFILIATION_MATCHER_API, json=body)

    if res.status_code == 202:
        return res.json().get("results")

    raise Exception(f"ERROR_{res.status_code}")


# api/match_list
def affiliations_get_matches(affiliations: pd.Series):

    affiliations = affiliations.fillna("").to_list()

    res = requests.post(
        url=AFFILIATION_MATCHER_LIST_API, json={"match_types": [MATCH_TYPE], "affiliations": affiliations}
    )

    if res.status_code == 202:
        task_id = res.json().get("data").get("task_id")
        print("task_id", task_id)

        results = affiliations_get_results(task_id)
        return pd.array(results, dtype="object")

    raise Exception(f"ERROR_{res.status_code}")


def affiliations_get_results(task_id: str):
    task_results = task_get_results(task_id)

    if task_results:
        results = task_get_matches(task_results, types=[MATCH_TYPE])
        return results

    raise Exception("NO TASK RESULTS")


@retry(wait=wait_fixed(60))
def task_get_results(task_id: str):
    task_response = requests.get(f"{AFFILIATION_MATCHER_LIST_TASK_API}/{task_id}")

    if task_response.status_code == 202:
        task_json = task_response.json()
        task_status = task_json.get("data").get("task_status")
        task_results = task_json.get("data").get("task_result")

        print("task_status", task_status)

        if task_status in ["queued", "started"]:
            raise Exception("TASK RUNNING")

        if task_status == "finished":
            return task_results


def task_get_matches(task_results, types=[]):
    task_matches = []
    for result in task_results:
        task_matches.append(result_get_matches(result, types))
    return task_matches


def result_get_matches(result, types=[]):
    result_matches = []
    api_matches = result.get("matches")
    if api_matches:
        for match in api_matches:
            match_type = match.get("type")
            match_id = match.get("id")
            if types and match_type in types:
                result_matches.append(match_id)
    return result_matches


# api/match
def affiliations_match(df: pd.DataFrame) -> pd.DataFrame:
    df[COL_AFFILIATION_MATCH] = df[COL_AFFILIATION_STR].apply(affiliation_get_matches)
    return df


# api/match_list
def affiliations_match_list(df: pd.DataFrame):
    df[COL_AFFILIATION_MATCH] = df[COL_AFFILIATION_STR].apply(affiliations_get_matches, by_row=False)
    return df


def affiliation_check_match(target_ids: list | str, match_ids: list):
    result = MATCH.ID_NO_MATCH if target_ids else MATCH.NO_ID_NO_MATCH

    if match_ids:
        if isinstance(target_ids, list):
            for id in target_ids:
                if id in match_ids:
                    result = MATCH.ID_MATCH
                    break
        else:
            if target_ids in match_ids:
                result = MATCH.ID_MATCH
            else:
                result = MATCH.ID_DIFF_MATCH if target_ids else MATCH.NO_ID_MATCH

    return result


def affiliation_is_match(paysage_row: pd.Series):
    target_id = paysage_row[COL_MATCH_ID]
    match_ids = paysage_row[COL_AFFILIATION_MATCH]

    return affiliation_check_match(target_id, match_ids)


def paysage_match_affiliations(match_type: str, use_match_list=False, use_acronym=False):
    print("Start affiliation matcher on Paysage structures.")
    print(f"Match type: {match_type}, use match list: {use_match_list}, use_acronym: {use_acronym}")

    if match_type not in ["rnsr", "paysage"]:
        raise ValueError(f"Matcher type should be 'rnsr' or 'paysage' (match_type={match_type})")

    if match_type == "paysage":
        globals()["MATCH_TYPE"] = match_type
        globals()["COL_MATCH_ID"] = COL_PAYSAGE_ID

    # Get paysage data from paysage api
    data = paysage_get_data()
    print(f"Found {len(data)} structures.")

    # Transform into clean dataframe
    df = paysage_transform_data(data)

    # Create affiliations strings
    df[COL_AFFILIATION_STR] = df.apply(paysage_get_affiliations, use_acronym=use_acronym, axis=1)
    print(f"Affiliations strings created.")

    # Match rnsr from affiliations strings
    df_match = affiliations_match_list(df) if use_match_list else affiliations_match(df)
    print("Affiliations strings matched.")

    # Check match
    df_match[COL_AFFILIATION_IS_MATCH] = df_match.apply(affiliation_is_match, axis=1)

    # Save results as json
    filename = f"paysage_match_list_{match_type}{'_acronym' if use_acronym else ''}.json"
    df_match.to_json(filename, default_handler=str)
    print(f"Results saved in {filename}")

    return 0


if __name__ == "__main__":
    args = sys.argv
    match_type = args[1]
    use_match_list = args[2].lower() == "true" if len(args) > 2 else False
    use_acronym = args[3].lower() == "true" if len(args) > 3 else False
    sys.exit(paysage_match_affiliations(match_type, use_match_list, use_acronym))
