from elasticsearch import Elasticsearch, helpers, RequestError

from matcher.server.main.config import ELASTICSEARCH_HOST, ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD
from matcher.server.main.logger import get_logger


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        if ELASTICSEARCH_LOGIN:
            self.logger.error('Using es login!')
            super().__init__(hosts=ELASTICSEARCH_HOST, http_auth=(ELASTICSEARCH_LOGIN, ELASTICSEARCH_PASSWORD))
        else:
            super().__init__(hosts=ELASTICSEARCH_HOST)

    def create_index(self, index: str = None, mappings: dict = None, settings: dict = None):
        if mappings is None:
            mappings = {}
        if settings is None:
            settings = {}
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        try:
            self.delete_index(index=index)
        except:
            pass
        try:
            response = self.indices.create(index=index, body={'mappings': mappings, 'settings': settings}, ignore=400)
        except RequestError as re:
            self.logger.error(f'Index creation failed : {re}')
            response = None
        return response

    def delete_index(self, index: str = None):
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        return self.indices.delete(index=index, ignore=404)

    def delete_all_by_query(self, index: str = None):
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        return self.delete_by_query(index=index, body={'query': {'match_all': {}}}, refresh=True)

    def parallel_bulk(self, actions: list = None) -> None:
        for success, info in helpers.parallel_bulk(client=self, actions=actions, request_timeout=60, refresh=True):
            if not success:
                self.logger.warning(f'A document failed: {info}')
