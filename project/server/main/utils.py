import os
import pandas as pd
import re
import requests
import shutil
import string
import unicodedata

from tempfile import mkdtemp
from zipfile import ZipFile

from project.server.main.logger import get_logger

logger = get_logger(__name__)

from project.server.main.config import CHUNK_SIZE, ZONE_EMPLOI_INSEE_DUMP, GEONAMES_DUMP_URL

ENGLISH_STOP = ['and', 'are', 'as', 'be', 'but', 'by', 'for', 'if', 'in', 'into', 'is', 'it', 'no',
                'not', 'of', 'on', 'or', 'such', 'that', 'the', 'their', 'then', 'there', 'these', 'they', 'this',
                'to', 'was', 'will', 'with']

FRENCH_STOP = ['au', 'aux', 'avec', 'ce', 'ces', 'dans', 'de', 'des', 'du', 'elle', 'en', 'et', 'eux', 'il', 'je', 'la',
               'le', 'leur', 'lui', 'ma', 'mais', 'me', 'même', 'mes', 'moi', 'mon', 'ne', 'nos', 'notre', 'nous', 'on',
               'ou', 'par', 'pas', 'pour', 'qu', 'que', 'qui', 'sa', 'se', 'ses', 'sur', 'ta', 'te', 'tes', 'toi',
               'ton', 'tu', 'un', 'une', 'vos', 'votre', 'vous', 'c', 'd', 'j', 'l', 'à', 'm', 'n', 's', 't', 'y', "'",
               'étée', 'étées', 'étant', 'suis', 'es', 'êtes', 'sont', 'serai', 'seras', 'sera', 'serons', 'serez',
               'seront', 'serais', 'serait', 'serions', 'seriez', 'seraient', 'étais', 'était', 'étions', 'étiez',
               'étaient', 'fus', 'fut', 'fûmes', 'fûtes', 'furent', 'sois', 'soit', 'soyons', 'soyez', 'soient',
               'fusse', 'fusses', 'fussions', 'fussiez', 'fussent', 'ayant', 'eu', 'eue', 'eues', 'eus', 'ai', 'avons',
               'avez', 'ont', 'aurai', 'aurons', 'aurez', 'auront', 'aurais', 'aurait', 'aurions', 'auriez', 'auraient',
               'avais', 'avait', 'aviez', 'avaient', 'eut', 'eûmes', 'eûtes', 'eurent', 'aie', 'aies', 'ait', 'ayons',
               'ayez', 'aient', 'eusse', 'eusses', 'eût', 'eussions', 'eussiez', 'eussent', 'ceci', 'cela', 'celà',
               'cet', 'cette', 'ici', 'ils', 'les', 'leurs', 'quel', 'quels', 'quelle', 'quelles', 'sans', 'soi']

GEO_IGNORED = ['union'] + FRENCH_STOP + ENGLISH_STOP

ACRONYM_IGNORED = (
    pd.read_csv("./project/server/main/acronym_to_ignore.csv")["acronyms"].to_list() + FRENCH_STOP + ENGLISH_STOP
)

NAME_IGNORED = ['medical center', 'medical college']

COUNTRY_SWITCHER = {
            'bn': ['brunei'],
            'ci': ['ivory coast'],
            'cv': ['cape verde'],
            'cz': ['czech'],
            'de': ['deutschland'],
            'gb': ['uk'],
            'ir': ['iran'],
            'kp': ['north korea'],
            'kr': ['south korea', 'republic of korea'],
            'la': ['laos'],
            'lb': ['liban'],
            'mo': ['macau'],
            'ru': ['russia'],
            'sy': ['syria'],
            'tw': ['taiwan'],
            'us': ['usa'],
            'vn': ['vietnam']
        }

CITY_COUNTRY = {
        'hong kong': ['hong kong']
    }

def remove_stop(text: str, stopwords: list) -> str:
    pattern = re.compile(r'\b(' + r'|'.join(stopwords) + r')\b\s*', re.IGNORECASE)
    return pattern.sub('', text)


def remove_parenthesis(x):
    if isinstance(x, str):
        return re.sub(r"[\(\[].*?[\)\]]", "", x)
    return x


def clean_list(
    data: list, stopwords=[], ignored=[], remove_inside_parenthesis=True, min_token=1, min_character=1
) -> list:
    # Cast data into list if needed
    if not isinstance(data, list):
        data = [data]
    data = list(filter(None, data))
    # Remove duplicates and non str
    data = [k for k in list(set(data)) if k and isinstance(k, str)]
    for ix, e in enumerate(data):
        if remove_inside_parenthesis:
            e = remove_parenthesis(e)
        if stopwords:
            e = remove_stop(e, stopwords)
        data[ix] = e.strip()
    new_data = []
    for k in data:
        k_normalized = normalize_text(k, remove_separator=False, to_lower=True)
        if k_normalized in ignored:
            continue
        if len(k_normalized) < min_character:
            continue
        if len(get_token_basic(k_normalized)) < min_token:
            continue
        new_data.append(k)
    return new_data


def chunks(lst: list, n: int) -> list:
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def get_token_basic(x):
    return x.split(' ')


def get_tokens(indices_client, analyzer: str, index: str, text: str) -> list:
    try:
        tokens = indices_client.analyze(body={'analyzer': analyzer, 'text': text}, index=index)['tokens']
    except:
        return [{'token': t} for t in text.split(' ')]
    return tokens


def remove_ref_index(query: str) -> str:
    """Remove the first 2 digits of a string if any."""
    if len(query.split(' ')) > 5:
        rgx = re.compile(r"^(\d){1,2}([A-Za-z])(.*)")
        return rgx.sub("\\2\\3", query).strip()
    return query.strip()


def strip_accents(text: str) -> str:
    """Normalize accents and stuff in string."""
    text = text.replace('’', ' ')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def delete_punctuation(text: str) -> str:
    """Delete all punctuation in a string."""
    return text.translate(str.maketrans(string.punctuation, len(string.punctuation) * " "))


def normalize_text(text: str = None, remove_separator: bool = True, re_order: bool = False, to_lower: bool = False) -> str:
    """Normalize string. Delete punctuation and accents."""
    if isinstance(text, str):
        text = text.replace('\xa0', ' ').replace('\n', ' ')
        text = delete_punctuation(text)
        text = strip_accents(text)
        if to_lower:
            text = text.lower()
        sep = '' if remove_separator else ' '
        text_split = text.split(' ')
        if re_order:
            text_split.sort()
        text = sep.join(text_split)
    return text.strip() or ""


def get_alpha2_from_french(user_input):
    ref = {
        'Afrique du Sud': 'za',
        'Argentine': 'ar',
        'Autriche': 'at',
        'Brésil': 'br',
        'Canada': 'ca',
        'Chili': 'cl',
        'Chine': 'cn',
        'Corée du Sud': 'kr',
        'Etats-Unis': 'us',
        'Ethiopie': 'et',
        'France': 'fr',
        'Inde': 'in',
        'Israël': 'il',
        'Italie': 'it',
        'Japon': 'jp',
        'Mexique': 'mx',
        'Pays-Bas': 'nl',
        'Russie': 'ru',
        'Sénégal': 'sn',
        'Singapour': 'sg'
    }
    return ref.get(user_input)


def download_geonames_data(country: str) -> dict:
    assert country.isupper() and len(country) == 2
    geonames_url = f"{GEONAMES_DUMP_URL}/{country}.zip"
    geonames_downloaded_file = f"{country}.zip"
    geonames_unzipped_folder = mkdtemp()
    geonames_unzipped_file = f"{geonames_unzipped_folder}/{country}.txt"
    COL_GEO_ID = 0  # Geoname ID column
    COL_FEAT_CLASS = 6  # Geoname feature class column http://www.geonames.org/export/codes.html
    COL_GEO_DEP = 11  # Department code column

    # Download file
    response = requests.get(url=geonames_url, stream=True, verify=False)
    with open(geonames_downloaded_file, "wb") as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    # Extract file
    with ZipFile(geonames_downloaded_file, "r") as file:
        file.extractall(geonames_unzipped_folder)

    # Read file
    df = pd.read_csv(
        geonames_unzipped_file,
        sep="\t",
        encoding="utf-8",
        dtype=str,
        header=None,
        usecols=[COL_GEO_ID, COL_FEAT_CLASS, COL_GEO_DEP],
    ).set_index(COL_GEO_ID)

    # Filter by feature class P = City, Village, ...
    df = df[df[COL_FEAT_CLASS] == "P"]

    # Correct department for Mayotte
    if country == "YT":
        df[COL_GEO_DEP] = "976"

    # Clean data
    data = df[COL_GEO_DEP].dropna().to_dict()

    os.remove(path=geonames_downloaded_file)
    shutil.rmtree(path=geonames_unzipped_folder)

    return data


def geonames_french_departments() -> dict:
    """Get geonames french departments

    Returns:
        data: dict(geoname_id: department code)
    """

    # France, Guadeloupe, Martinique, Guyane, Reunion, Mayotte
    french_codes = ["FR", "GP", "MQ", "GF", "RE", "YT"]
    logger.debug(f"Start download of geonames for countries {french_codes}")

    data = {}
    for code in french_codes:
        try:
            current_data = download_geonames_data(country=code)
            data.update(current_data)
        except Exception as error:
            logger.error(f"Error while loading geonames {code} data: {error}")

    return data


def download_insee_data() -> list:
    insee_downloaded_file = 'insee_data_dump.zip'
    insee_unzipped_folder = mkdtemp()
    response = requests.get(url=ZONE_EMPLOI_INSEE_DUMP, stream=True, verify=False)
    with open(insee_downloaded_file, 'wb') as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)
    with ZipFile(insee_downloaded_file, 'r') as file:
        file.extractall(insee_unzipped_folder)
    data = pd.read_excel(
        f"{insee_unzipped_folder}/ZE2020_au_01-01-2024.xlsx",
        sheet_name="Composition_communale",
        engine="calamine",
        skiprows=5,
    ).to_dict(orient="records")
    os.remove(path=insee_downloaded_file)
    shutil.rmtree(path=insee_unzipped_folder)
    return data


def insee_zone_emploi_data(use_city_key=False) -> tuple[dict, dict]:
    """Transform INSEE zone emploi data into multiple dicts

    Args:
        use_city_key (bool, optional): Use city key ('dep_cityname') instead of city_code. Defaults to False.

    Returns:
        zone_emploi: dict(zone_emploi_code: {"name": zone_emploi_name, "composition": [city_names])
        city_zone_emploi: dict(city_code: zone_emploi_name)
    """

    city_zone_emploi = {}
    zone_emploi = {}

    logger.debug(f"Load insee data")

    try:
        zone_emploi_insee = download_insee_data()

        for elem in zone_emploi_insee:
            city_name = elem["LIBGEO"]
            city_code = str(elem["CODGEO"])
            city_dep = str(elem["DEP"])
            city_dep = "20" if city_dep in ["2A", "2B"] else city_dep  # Corse
            city_key = city_dep + "_" + normalize_text(city_name, remove_separator=False, to_lower=True)
            zone_emploi_name = elem["LIBZE2020"]
            zone_emploi_code = str(elem["ZE2020"])

            # Build zone emploi composition dict
            if zone_emploi_code not in zone_emploi:
                zone_emploi[zone_emploi_code] = {"name": zone_emploi_name, "composition": []}
            zone_emploi[zone_emploi_code]["composition"].append(city_name)

            # Build city zone emploi dict
            key = city_key if use_city_key else city_code
            city_zone_emploi.setdefault(key, zone_emploi_code)

    except Exception as error:
        logger.error(f"Error while loading insee data: {error}")

    return zone_emploi, city_zone_emploi


def has_a_digit(text: str = '') -> bool:
    for char in text:
        if char.isdigit():
            return True
    return False


def get_common_words(objects: list, field: string, split: bool = True, threshold: int = 10) -> list:
    dictionary = {}
    for obj in objects:
        for text in obj.get(field, []):
            if split:
                words = normalize_text(text=text, remove_separator=False).split(' ')
            else:
                words = [normalize_text(text=text, remove_separator=False)]
            for word in words:
                if word not in dictionary:
                    dictionary[word] = 0
                dictionary[word] += 1
    result = []
    for entry in dictionary:
        if dictionary[entry] >= threshold:
            result.append(entry)
    return result

def clean_url(x):
    if not isinstance(x, str):
        return None
    x = x.lower().strip()
    for f in ['https://', 'http://', 'www.']:
        x = x.replace(f, '')
    if len(x)> 0 and x[-1] == '/':
        x = x[:-1]
    return x

def get_url_domain(x):
    url = clean_url(x)
    return url.split('/')[0]


def clean_city(city: str):
    if not isinstance(city, str):
        return None
    clean_city = re.sub("(?i)c(é|e)dex", "", city)  # Remove CEDEX
    clean_city = " ".join([s for s in clean_city.split(" ") if not s.isnumeric()])
    return clean_city.strip()
