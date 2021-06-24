from matcher.server.main.init_wikidata import data2actions, get_cities_from_wikidata, get_hospitals_from_wikidata,\
    get_universities_from_wikidata, init_wikidata
from matcher.server.main.my_elastic import MyElastic


class TestInitWikidata:
    def test_get_cities_from_wikidata(self) -> None:
        cities = get_cities_from_wikidata()
        assert len(cities) == 6778
        keys = list(cities[0].keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_es', 'label_fr', 'label_it', 'label_native',
                        'label_official']

    def test_get_hospitals_from_wikidata(self) -> None:
        hospitals = get_hospitals_from_wikidata()
        assert len(hospitals) == 40215
        keys = list(hospitals[0].keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_es', 'label_fr', 'label_it']

    def test_get_universities_from_wikidata(self) -> None:
        universities = get_universities_from_wikidata()
        assert len(universities) == 54935
        keys = list(universities[0].keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_es', 'label_fr', 'label_it', 'label_native']

    def test_data2actions(self) -> None:
        index = 'test_wikidata'
        data = {{'country_alpha2': {'value': 'FR'}, 'label_en': {'value': 'label_01_EN'},
                 'label_fr': {'value': 'label_01_FR'}}}
        actions = data2actions(index=index, data=data)
        assert len(actions) == 2
        assert actions[0] == {'_index': index, 'country_alpha2': 'fr', 'query': {'match_phrase': {'content': {
            'query': 'label_01_EN', 'analyzer': 'standard'}}}}

    def test_wikidata_country(self, requests_mock) -> None:
        requests_mock.real_http = True
        requests_mock.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql',
                          json={'results': {'bindings': [
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_01'}},
                              {'country_alpha2': {'value': 'de'}, 'label_native': {'value': 'value_02'}},
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_03'}}
                          ]}})
        es = MyElastic()
        init_wikidata(index_prefix='test_')
        french_universities = es.search(index='test_wikidata_universities',
                                        body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert french_universities['hits']['total']['value'] == 2
