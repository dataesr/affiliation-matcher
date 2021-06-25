from matcher.server.main.load_grid import load_grid
from matcher.server.main.my_elastic import MyElastic


class TestLoadGrid:
    def test_load_grid(self) -> None:
        es = MyElastic()
        load_grid(index_prefix='test')
        french_cities = es.search(index='test_grid_city', body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert french_cities['hits']['total']['value'] == 629
        paris = es.search(index='test_grid_city', body={'query': {'percolate': {'field': 'query',
                                                                                'document': {'content': 'Paris'}}}})
        assert paris['hits']['total']['value'] == 3
        es.delete_index(index='test_grid_city')
        es.delete_index(index='test_grid_institution')
        es.delete_index(index='test_grid_institution_acronym')
