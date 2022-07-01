import os
import requests

from project.server.main.logger import get_logger

logger = get_logger(__name__)


def get_last_ror_dump_url():
    try:
        ROR_URL = 'https://zenodo.org/api/records/?communities=ror-data&sort=mostrecent'
        response = requests.get(url=ROR_URL).json()
        ror_dump_url = response['hits']['hits'][0]['files'][-1]['links']['self']
        logger.debug(f'Last ROR dump url found: {ror_dump_url}')
    except:
        ror_dump_url = 'https://zenodo.org/api/files/25d4f93f-6854-4dd4-9954-173197e7fad7/v1.1-2022-06-16-ror-data.zip'
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

GRID_DUMP_URL = 'https://digitalscience.figshare.com/ndownloader/files/30895309'
SCANR_DUMP_URL = 'https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/scanR/organizations.json'
ZONE_EMPLOI_INSEE_DUMP = 'https://www.insee.fr/fr/statistiques/fichier/4652957/ZE2020_au_01-01-2021.zip'

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
    ELASTICSEARCH_URL = f'{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}'
