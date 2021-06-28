from matcher.server.main.load_wikidata import data2actions, get_cities_from_wikidata, get_hospitals_from_wikidata, \
    get_universities_from_wikidata, load_wikidata
from matcher.server.main.my_elastic import MyElastic


class TestLoadWikidata:
    def test_get_cities_from_wikidata(self) -> None:
        cities = get_cities_from_wikidata()
        assert len(cities) == 6774
        city = [city for city in cities if city.get('label_fr', {}).get('value') == 'Nantes'][0]
        keys = list(city.keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_es', 'label_fr', 'label_it', 'label_native',
                        'label_official']

    def test_get_hospitals_from_wikidata(self) -> None:
        hospitals = get_hospitals_from_wikidata()
        assert len(hospitals) == 40222
        hospital = [hospital for hospital in hospitals if hospital.get('label_fr', {}).get('value') ==
                    'Massachusetts General Hospital'][0]
        keys = list(hospital.keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_es', 'label_fr', 'label_it']

    def test_get_universities_from_wikidata(self) -> None:
        universities = get_universities_from_wikidata()
        assert len(universities) == 54944
        university = [university for university in universities if university.get('label_en', {}).get('value') ==
                      'New York University Tandon School of Engineering'][0]
        keys = list(university.keys())
        keys.sort()
        assert keys == ['country_alpha2', 'label_en', 'label_fr', 'label_it', 'label_native']

    def test_data2actions(self) -> None:
        index = 'test_wikidata'
        data = [{'country_alpha2': {'value': 'FR'}, 'label_en': {'value': 'label_01_EN'},
                 'label_fr': {'value': 'label_01_FR'}}]
        actions = data2actions(index=index, data=data)
        assert len(actions) == 2
        assert actions[0]['_index'] == index
        assert actions[0]['country_alpha2'] == 'fr'
        assert actions[0]['query']['match_phrase']['content']['query'] in ['label_01_EN', 'label_01_FR']

    def test_load_wikidata(self, requests_mock) -> None:
        requests_mock.real_http = True
        requests_mock.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql',
                          json={'results': {'bindings': [
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_01'}},
                              {'country_alpha2': {'value': 'de'}, 'label_native': {'value': 'value_02'}},
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_03'}}
                          ]}})
        es = MyElastic()
        load_wikidata(index_prefix='test')
        french_universities = es.search(index='test_wikidata_university',
                                        body={'query': {'match': {'country_alpha2': 'fr'}}})
        assert french_universities['hits']['total']['value'] == 2
        es.delete_index('test_wikidata_city')
        es.delete_index('test_wikidata_hospital')
        es.delete_index('test_wikidata_university')
