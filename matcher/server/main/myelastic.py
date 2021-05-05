from elasticsearch import Elasticsearch

from matcher.server.main.config import config


class MyElastic(Elasticsearch):
    def __init__(self) -> None:
        super().__init__(hosts=config['ELASTICSEARCH_HOST'])

    def create_index(self, index: str = None, mapping: dict =None) -> None:
        if mapping is None:
            mapping = {}
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        self.delete_index(index=index)
        return self.indices.create(index=index, body=mapping, ignore=400)

    def delete_index(self, index: str = None) -> None:
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        return self.indices.delete(index=index, ignore=404)

    def my_index(self, index: str = None, id: str = None, body: dict = None) -> bool:
        if index is None or id is None:
            raise ValueError('Empty value passed for a required argument "index" or "id".')
        return self.index(index=index, id=id, body=body, refresh=True)

    def my_search(self, index: str = None, body: dict = None) -> bool:
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        if body is None:
            body = {'query': {'match_all': {}}}
        return self.search(index=index, body=body)

    def my_delete_by_query(self, index: str = None, body: dict = None) -> bool:
        if index is None:
            raise ValueError('Empty value passed for a required argument "index".')
        if body is None:
            body = {'query': {'match_all': {}}}
        return self.delete_by_query(index=index, body=body, refresh=True)
