import os
import sys
import requests
import pandas as pd
import numpy as np
from enum import Enum
from tenacity import retry, wait_fixed
from dotenv import load_dotenv

load_dotenv()

ODS_API_KEY = os.getenv("ODS_API_KEY")
ODS_PAYSAGE_KEY = os.getenv("ODS_PAYSAGE_KEY")

AFFILIATION_MATCHER_API = f"{os.getenv('AFFILIATION_MATCHER_URL')}/match"
AFFILIATION_MATCHER_LIST_API = "http://localhost:5004/match_list"
AFFILIATION_MATCHER_LIST_TASK_API = "http://localhost:5004/tasks"

MATCH_TYPE_RNSR = "rnsr"
COL_RNSR_ID = "identifiant_rnsr"
COL_PAYSAGE_ID = "identifiant_interne"
COL_STATE = "etat"
COL_YEAR = "date_fermeture"
COL_ACRONYM = "sigle"
COL_COUNTRY = "pays_etranger_acheminement"
SUBSET_NAMES = ["uo_lib", "uo_lib_officiel"]
SUBSET_ADRESS = [
    "adresse_uai",
    "lieu_dit_uai",
    "boite_postale_uai",
    "code_postal_uai",
    "localite_acheminement_uai",
    COL_COUNTRY,
]
SUBSET_ALL = [COL_RNSR_ID, COL_PAYSAGE_ID, COL_STATE, COL_YEAR, COL_ACRONYM] + SUBSET_NAMES + SUBSET_ADRESS

COL_AFFILIATION_STR = "affiliation_string"
COL_AFFILIATION_STR_OFF = "affiliation_string_off"
SUBSET_AFFILIATION_STR = [COL_AFFILIATION_STR, COL_AFFILIATION_STR_OFF]
COL_AFFILIATION_MATCH = "affiliation_match"
COL_AFFILIATION_MATCH_OFF = "affiliation_match_off"
SUBSET_AFFILIATION_MATCH = [COL_AFFILIATION_MATCH, COL_AFFILIATION_MATCH_OFF]
COL_AFFILIATION_IS_MATCH = "affiliation_is_match"
COL_AFFILIATION_IS_MATCH_OFF = "affiliation_is_match_off"


class MATCH(Enum):
    NO_ID_NO_MATCH = 0
    ID_NO_MATCH = 1
    ID_MATCH = 2
    ID_DIFF_MATCH = 3
    NO_ID_MATCH = 6


def ods_get_df(ods_key: str, subset=None):
    df = pd.read_csv(
        f"https://data.enseignementsup-recherche.gouv.fr/explore/dataset/{ods_key}/download/?format=csv&apikey={ODS_API_KEY}",
        sep=";",
        low_memory=False,
    )

    columns = df.columns.tolist()

    if COL_STATE in columns:
        # Set state as boolean
        df[COL_STATE] = df[COL_STATE].apply(lambda state: True if state == "Actif" else False).astype(bool)

    if COL_YEAR in columns:
        # Keep only year
        df[COL_YEAR] = df[COL_YEAR].apply(lambda date: date[:4] if isinstance(date, str) else None)

    if subset:
        return df[subset].copy()

    return df


def paysage_get_names(paysage_row: pd.Series, use_acronym=False):
    names = paysage_row[SUBSET_NAMES]
    names = names.where(~names.duplicated(), "").to_list()

    if use_acronym:
        acronym = paysage_row[COL_ACRONYM]
        names = [f"{acronym} - {name}" if isinstance(acronym, str) else name for name in names]

    return names


def paysage_get_adress(paysage_row: pd.Series):
    adress = paysage_row[SUBSET_ADRESS].dropna().to_list()
    adress_str = ", ".join(adress)
    return adress_str


def paysage_get_affiliations(paysage_row: pd.Series, use_acronym=False):
    names = paysage_get_names(paysage_row, use_acronym)
    adress = paysage_get_adress(paysage_row)
    affiliations = [f"{name}, {adress}" if name else None for name in names]
    return pd.Series(affiliations)


# api/match
def affiliation_get_matches(affiliation: str, year=None):
    if not affiliation:
        return []

    body = {"type": MATCH_TYPE_RNSR, "query": affiliation}
    if year:
        body["year"] = year

    res = requests.post(url=AFFILIATION_MATCHER_API, json=body)

    if res.status_code == 202:
        return res.json().get("results")

    raise Exception("ERROR_{res.status_code}")


# api/match_list
def affiliations_get_matches(affiliations: pd.Series):
    affiliations = affiliations.fillna("").to_list()

    res = requests.post(
        url=AFFILIATION_MATCHER_LIST_API, json={"match_types": [MATCH_TYPE_RNSR], "affiliations": affiliations}
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
        results = task_get_matches(task_results, types=[MATCH_TYPE_RNSR])
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
    df[COL_AFFILIATION_MATCH_OFF] = df[COL_AFFILIATION_STR_OFF].apply(affiliation_get_matches)
    return df


# api/match_list
def affiliations_match_list(df: pd.DataFrame):
    df[SUBSET_AFFILIATION_MATCH] = df[SUBSET_AFFILIATION_STR].apply(affiliations_get_matches)
    return df


def affiliation_check_match(rnsr_id: str, match_ids: list):
    result = MATCH.ID_NO_MATCH if rnsr_id else MATCH.NO_ID_NO_MATCH

    if match_ids:
        if rnsr_id in match_ids:
            result = MATCH.ID_MATCH
        else:
            result = MATCH.ID_DIFF_MATCH if rnsr_id else MATCH.NO_ID_MATCH

    return result


def affiliation_is_match(paysage_row: pd.Series):
    rnsr_id = paysage_row[COL_RNSR_ID]
    match_ids = paysage_row[COL_AFFILIATION_MATCH]

    return affiliation_check_match(rnsr_id, match_ids)


def affiliation_is_match_off(paysage_row: pd.Series):
    rnsr_id = paysage_row[COL_RNSR_ID]
    affiliation_off = paysage_row[COL_AFFILIATION_STR_OFF]
    match_ids = paysage_row[COL_AFFILIATION_MATCH_OFF]

    if not affiliation_off:
        return None

    return affiliation_check_match(rnsr_id, match_ids)


def paysage_match_rnsr(use_match_list=False, use_acronym=False):
    print("Start affiliation matcher on Paysage structures.")
    print(f"Use match list: {use_match_list}, use_acronym: {use_acronym}")

    # Get paysage data from ods
    df = ods_get_df(ODS_PAYSAGE_KEY, SUBSET_ALL)
    print(f"Found {len(df)} structures.")

    # Filter with France structures
    df = df[df[COL_COUNTRY] == "France"].replace(np.nan, None).copy()
    print(f"Found {len(df)} french structures.")

    # Create affiliations strings
    df[SUBSET_AFFILIATION_STR] = df.apply(paysage_get_affiliations, use_acronym=use_acronym, axis=1)
    print(f"Affiliations strings created.")

    # Match rnsr from affiliations strings
    df_match = affiliations_match_list(df) if use_match_list else affiliations_match(df)
    print("Affiliations strings matched.")

    # Check with rnsr id from paysage
    df_match[COL_AFFILIATION_IS_MATCH] = df_match.apply(affiliation_is_match, axis=1)
    df_match[COL_AFFILIATION_IS_MATCH_OFF] = df_match.apply(affiliation_is_match_off, axis=1)

    # Save results as json
    filename = f"paysage_match_list{'_acronym' if use_acronym else ''}.json"
    df_match.to_json(filename, default_handler=str)
    print(f"Results saved in {filename}")

    return 0


if __name__ == "__main__":
    args = sys.argv
    use_match_list = args[1] if len(args) > 1 else False
    use_acronym = args[2] if len(args) > 2 else False
    sys.exit(paysage_match_rnsr(use_match_list, use_acronym))
