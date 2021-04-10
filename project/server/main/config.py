import os

# Load the application environment
APP_ENV = os.getenv('APP_ENV', 'development')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
ELASTICSEARCH_HOST = 'localhost'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_INDEX = 'index-rnsr-all'
OPENCAGE_API_KEY = '717bb9b3d9d749daa064c8cb5f90051d'

if APP_ENV in ['staging', 'production']:
    ELASTICSEARCH_HOST = 'elasticsearch'

if APP_ENV in ['test']:
    ELASTICSEARCH_INDEX = 'index-rnsr-test'

ELASTICSEARCH_URL = ELASTICSEARCH_HOST + ':' + ELASTICSEARCH_PORT

# Export config
config = {
    'APP_ENV': APP_ENV,
    'APP_ORGA': APP_ORGA,
    'ELASTICSEARCH_HOST': ELASTICSEARCH_HOST,
    'ELASTICSEARCH_INDEX': ELASTICSEARCH_INDEX,
    'ELASTICSEARCH_PORT': ELASTICSEARCH_PORT,
    'ELASTICSEARCH_URL': ELASTICSEARCH_URL,
    'OPENCAGE_API_KEY': OPENCAGE_API_KEY
}
