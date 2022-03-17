from project.server.main.load_grid import load_grid
from project.server.main.my_elastic import MyElastic


class TestLoadGrid:
    def test_load_grid(self) -> None:
        es = MyElastic()
        load_grid(index_prefix='test')
        french_cities = es.search(index='test_grid_city', body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert 600 < french_cities['hits']['total']['value'] < 700
        paris = es.search(index='test_grid_city', body={'query': {'percolate': {'field': 'query',
                                                                                'document': {'content': 'Paris'}}}})
        assert len(paris['hits']['hits'][0]['_source']['country_alpha2']) == 3
        es.delete_index(index='test_grid_*')
