from matcher.server.main.init_grid import init_grid
from matcher.server.main.my_elastic import MyElastic


class TestInitGrid:
    def test_init_country(self) -> None:
        es = MyElastic()
        init_grid(index_prefix='test_')
        french_cities = es.search(index='test_grid_cities', body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert french_cities['hits']['total']['value'] == 629
        paris = es.search(index='test_grid_cities', body={'query': {'percolate': {'field': 'query',
                                                                                  'document': {'content': 'Paris'}}}})
        assert paris['hits']['total']['value'] == 3
        es.delete_index(index='test_grid_cities')
        es.delete_index(index='test_grid_institutions')
        es.delete_index(index='test_grid_institutions_acronyms')
