from elasticsearch import Elasticsearch, helpers

from matcher.server.main.config import ELASTICSEARCH_HOST, ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD
from matcher.server.main.logger import get_logger


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        if ELASTICSEARCH_LOGIN:
            super().__init__(hosts=ELASTICSEARCH_HOST, http_auth=(ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD), timeout=30, max_retries=10, retry_on_timeout=True)
        else:
            super().__init__(hosts=ELASTICSEARCH_HOST, timeout=30, max_retries=10, retry_on_timeout=True)

    def exception_handler(func):
        def inner_function(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exception:
                self.logger.error(f'{func.__name__} raises an error through decorator "exception_handler".')
                self.logger.error(exception)
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
                self.logger.warning(f'A document failed: {info}')
