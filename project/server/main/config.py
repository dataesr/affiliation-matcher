import os

# Load the application environment
APP_ENV = os.getenv('APP_ENV', 'local')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
ELASTICSEARCH_HOST = 'localhost'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_INDEX = 'index-rnsr-all'

if APP_ENV in ['staging', 'production']:
    ELASTICSEARCH_HOST = 'elasticsearch'

if APP_ENV in ['test']:
    ELASTICSEARCH_INDEX = 'test'

ELASTICSEARCH_URL = ELASTICSEARCH_HOST + ':' + ELASTICSEARCH_PORT

# Export config
config = {
    'APP_ORGA': APP_ORGA,
    'ELASTICSEARCH_HOST': ELASTICSEARCH_HOST,
    'ELASTICSEARCH_INDEX': ELASTICSEARCH_INDEX,
    'ELASTICSEARCH_PORT': ELASTICSEARCH_PORT,
    'ELASTICSEARCH_URL': ELASTICSEARCH_URL
}
