import os

# Load the application environment
APP_ENV = os.getenv('APP_ENV', 'local')

# Set default config
APP_ORGA = 'http://185.161.45.213/organizations'
ELASTICSEARCH_HOST = 'localhost'
ELASTICSEARCH_PORT = '9200'

if APP_ENV == 'production':
    ELASTICSEARCH_HOST = 'elasticsearch'
elif APP_ENV == 'staging':
    ELASTICSEARCH_HOST = 'elasticsearch'

ELASTICSEARCH_URL = ELASTICSEARCH_HOST + ':' + ELASTICSEARCH_PORT

# Export config
config = {
    'APP_ORGA': APP_ORGA,
    'ELASTICSEARCH_HOST': ELASTICSEARCH_HOST,
    'ELASTICSEARCH_PORT': ELASTICSEARCH_PORT,
    'ELASTICSEARCH_URL': ELASTICSEARCH_URL
}
