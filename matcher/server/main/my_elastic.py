from elasticsearch import Elasticsearch, helpers

from matcher.server.main.config import ELASTICSEARCH_HOST
from matcher.server.main.logger import get_logger


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        super().__init__(hosts=ELASTICSEARCH_HOST)
        self.logger = get_logger(__name__)

    def create_index(self, index: str = None, mappings: dict = None, settings: dict = None) -> None:
        if mappings is None:
            mappings = {}
        if settings is None:
            settings = {}
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        self.delete_index(index=index)
        return self.indices.create(index=index, body={'mappings': mappings, 'settings': settings}, ignore=400)

    def delete_index(self, index: str = None) -> None:
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        return self.indices.delete(index=index, ignore=404)

    def delete_all_by_query(self, index: str = None) -> None:
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        return self.delete_by_query(index=index, body={'query': {'match_all': {}}}, refresh=True)

    def parallel_bulk(self, actions: list = None) -> None:
        for success, info in helpers.parallel_bulk(client=self, actions=actions, request_timeout=60, refresh=True):
            if not success:
                self.logger.warning(f'A document failed: {info}')
