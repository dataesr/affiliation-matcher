from matcher.server.main.load_country import load_country
from matcher.server.main.my_elastic import MyElastic

class TestLoadCountry:
    def test_load_country(self) -> None:
        es = MyElastic()
        load_country(index_prefix='test')
        fra = es.search(index='test_country_alpha3', body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert fra['hits']['total']['value'] == 1
        japan = es.search(index='test_country_all_names', body={'query': {'percolate': {'field': 'query',
                                                                                'document': {'content': 'Japan'}}}})
        assert japan['hits']['hits'][0]['_source']['country_alpha2'] == ['JP']
        es.delete_index(index='test_country_*')
