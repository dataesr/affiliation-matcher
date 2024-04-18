from elasticsearch import Elasticsearch, helpers

from project.server.main.config import ELASTICSEARCH_HOST, ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD
from project.server.main.logger import get_logger

logger = get_logger(__name__)


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        if ELASTICSEARCH_LOGIN:
            super().__init__(hosts=ELASTICSEARCH_HOST, http_auth=(ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD),
                             timeout=30, max_retries=10, retry_on_timeout=True)
        else:
            super().__init__(hosts=ELASTICSEARCH_HOST, timeout=30, max_retries=10, retry_on_timeout=True)

    def exception_handler(func):
        def inner_function(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exception:
                logger.error(f'{func.__name__} raises an error through decorator "exception_handler".')
                logger.error(exception)
                return None
        return inner_function

    @exception_handler
    def create_index(self, index: str = None, mappings: dict = None, settings: dict = None):
        if mappings is None:
            mappings = {}
        if settings is None:
            settings = {}
        self.delete_index(index=index)
        response = self.indices.create(index=index, body={'mappings': mappings, 'settings': settings}, ignore=400)
        return response

    @exception_handler
    def delete_index(self, index: str = None):
        return self.indices.delete(index=index, ignore=404)

    @exception_handler
    def delete_all_by_query(self, index: str = None):
        return self.delete_by_query(index=index, body={'query': {'match_all': {}}}, refresh=True)

    @exception_handler
    def parallel_bulk(self, actions: list = None) -> None:
        for success, info in helpers.parallel_bulk(client=self, actions=actions, request_timeout=60, refresh=True):
            if not success:
                logger.warning(f'A document failed: {info}')

    @exception_handler
    def delete_non_dated_indices(self, index_prefix):
        for idx in list(self.indices.get('*').keys()):
            if idx.startswith(index_prefix):
                idx_splitted = idx.replace(index_prefix, '').split('-')
                try:
                    current_date = int(idx_splitted[1][0:14])
                    assert(20220601000000 < current_date < 25000101000000)
                except:
                    logger.debug(f'{idx} is not a dated index, lets delete it')
                    self.indices.delete(index=idx, ignore=[400, 404])

    @exception_handler
    def update_index_alias(self, my_alias, new_index):
        logger.debug(f'update_index_alias {my_alias} {new_index}')
        old_index = None
        aliases_data = self.indices.get_alias('*')
        # logger.debug('aliases_data')
        # logger.debug(aliases_data)
        for idx in aliases_data:
            if my_alias in list(aliases_data[idx]['aliases'].keys()):
                old_index = idx
                break
        actions = []
        if old_index:
            actions.append({'remove': {'index': old_index, 'alias': my_alias}})
            logger.debug(f'remove alias {my_alias} for index {old_index}')
        else:
            logger.debug(f'no index for alias {my_alias}')
        actions.append({'add': {'index': new_index, 'alias': my_alias}})
        logger.debug(f'add alias {my_alias} for index {new_index}')
        self.indices.update_aliases({'actions': actions})

        if old_index:
            logger.debug(f'delete index {old_index}')
            self.indices.delete(index=old_index, ignore=[400, 404])
