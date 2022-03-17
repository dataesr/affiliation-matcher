from project.server.main.load_ror import load_ror
from project.server.main.my_elastic import MyElastic


class TestLoadRor:
    def test_load_ror(self) -> None:
        es = MyElastic()
        index_prefix = 'test'
        load_ror(index_prefix=index_prefix)
        french_cities = es.search(
            index=f'{index_prefix}_ror_city',
            body={'query': {'match': {'country_alpha2': 'fr'}}}
        )
        assert french_cities['hits']['total']['value'] < 650
        paris = es.search(
            index=f'{index_prefix}_ror_city',
            body={'query': {'percolate': {'field': 'query',
                  'document': {'content': 'Paris'}}}})
        assert len(paris['hits']['hits'][0]['_source']['country_alpha2']) == 3
        es.delete_index(index=f'{index_prefix}_ror_*')
