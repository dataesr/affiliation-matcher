import os
import requests

from project.server.main.logger import get_logger

logger = get_logger(__name__)


def get_last_ror_dump_url():
    ROR_URL = "https://zenodo.org/api/communities/ror-data/records?q=&sort=newest"
    response = requests.get(url=ROR_URL).json()
    ror_dump_url = response['hits']['hits'][0]['files'][-1]['links']['self']
    logger.debug(f'Last ROR dump url found: {ror_dump_url}')
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
SCANR_DUMP_URL = 'https://scanr-data.s3.gra.io.cloud.ovh.net/production/organizations.jsonl.gz'
ZONE_EMPLOI_INSEE_DUMP = 'https://www.insee.fr/fr/statistiques/fichier/4652957/ZE2020_au_01-01-2024.zip'
GEONAMES_DUMP_URL = "https://download.geonames.org/export/dump"

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
