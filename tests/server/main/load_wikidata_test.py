from project.server.main.load_wikidata import data2actions, load_wikidata
from project.server.main.my_elastic import MyElastic


class TestLoadWikidata:
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
        es.delete_index('test_wikidata_*')
