import os
import requests
from bs4 import BeautifulSoup
from matcher.server.main.logger import get_logger
        
logger = get_logger(__name__)

# Load the application environment
APP_ENV = os.getenv('APP_ENV')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
ELASTICSEARCH_HOST = 'elasticsearch'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_INDEX = 'index-rnsr-all'
GRID_URL = "https://www.grid.ac/downloads"

try:
    soup = BeautifulSoup(requests.get(GRID_URL).text, "lxml")
    GRID_DUMP_URL = soup.find('a', class_="btn-red")['href'].strip()
    logger.debug(f"last grid dump url found: {GRID_DUMP_URL}")
except:
    GRID_DUMP_URL = "https://ndownloader.figshare.com/files/28431024"
    logger.error(f"grid dump url detection failed, using {GRID_DUMP_URL} instead")

SCANR_DUMP_URL = 'https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/scanR/organizations.json'

if APP_ENV == 'test':
    ELASTICSEARCH_HOST = 'localhost'
    ELASTICSEARCH_INDEX = 'index-rnsr-test'

if APP_ENV == 'development':
    ELASTICSEARCH_HOST = 'localhost'

ELASTICSEARCH_URL = ELASTICSEARCH_HOST + ':' + ELASTICSEARCH_PORT

# Export config
config = {
    'APP_ENV': APP_ENV,
    'APP_ORGA': APP_ORGA,
    'ELASTICSEARCH_HOST': ELASTICSEARCH_HOST,
    'ELASTICSEARCH_INDEX': ELASTICSEARCH_INDEX,
    'ELASTICSEARCH_PORT': ELASTICSEARCH_PORT,
    'ELASTICSEARCH_URL': ELASTICSEARCH_URL,
    'GRID_DUMP_URL': GRID_DUMP_URL,
    'SCANR_DUMP_URL': SCANR_DUMP_URL
}
