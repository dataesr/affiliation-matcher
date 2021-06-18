import os

# Load the application environment
APP_ENV = os.getenv('APP_ENV')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
ELASTICSEARCH_HOST = 'elasticsearch'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_INDEX = 'index-rnsr-all'
GRID_DUMP_URL = 'https://ndownloader.figshare.com/files/27251693'
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
