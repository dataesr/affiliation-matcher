from elasticsearch import Elasticsearch

from matcher.server.main.config import config


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        super().__init__(hosts=config['ELASTICSEARCH_HOST'])

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
