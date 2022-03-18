import os
import requests

from bs4 import BeautifulSoup

from project.server.main.logger import get_logger

logger = get_logger(__name__)


def get_last_grid_dump_url():
    try:
        soup = BeautifulSoup(requests.get(GRID_URL).text, 'lxml')
        grid_dump_url = soup.find('a', class_='btn-red')['href'].strip()
        logger.debug(f'Last grid dump url found: {grid_dump_url}')
    except:
        grid_dump_url = 'https://ndownloader.figshare.com/files/30895309'
        logger.error(f'Grid dump url detection failed, using {grid_dump_url} instead')
    return grid_dump_url


def get_last_ror_dump_url():
    try:
        ROR_URL = 'https://zenodo.org/api/records/?communities=ror-data&sort=mostrecent'
        response = requests.get(url=ROR_URL).json()
        ror_dump_url = response['hits']['hits'][0]['files'][0]['links']['self']
        logger.debug(f'Last ROR dump url found: {ror_dump_url}')
    except:
        ror_dump_url = 'https://github.com/ror-community/ror-api/blob/master/rorapi/data/ror-2021-09-23/ror.zip?' \
                       'raw=true'
        logger.error(f'ROR dump url detection failed, using {ror_dump_url} instead')
    return ror_dump_url


# Load the application environment
APP_ENV = os.getenv('APP_ENV')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
CHUNK_SIZE = 128
ELASTICSEARCH_HOST = 'elasticsearch'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_LOGIN = None
ELASTICSEARCH_PASSWORD = None

GRID_URL = 'https://www.grid.ac/downloads'
SCANR_DUMP_URL = 'https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/scanR/organizations.json'
ZONE_EMPLOI_INSEE_DUMP = 'https://www.insee.fr/fr/statistiques/fichier/4652957/ZE2020_au_01-01-2021.zip'

GRID_DUMP_URL = get_last_grid_dump_url()
ROR_DUMP_URL = get_last_ror_dump_url()


if APP_ENV == 'test':
    ELASTICSEARCH_HOST = 'localhost'
elif APP_ENV == 'development':
    ELASTICSEARCH_HOST = 'elasticsearch'
elif APP_ENV == 'production':
    ELASTICSEARCH_HOST = os.getenv('ES_URL')
    ELASTICSEARCH_URL = ELASTICSEARCH_HOST
    ELASTICSEARCH_LOGIN = os.getenv('ES_LOGIN_MATCHER')
    ELASTICSEARCH_PASSWORD = os.getenv('ES_PASSWORD_MATCHER')
else:
    ELASTICSEARCH_URL = ELASTICSEARCH_HOST + ':' + ELASTICSEARCH_PORT
