import pytest

from matcher.server.main.init_country import get_cities_from_insee, get_cities_from_wikidata, \
    get_universities_from_mesri, get_universities_from_wikidata, get_names_from_country, get_hospitals_from_wikidata,\
    init_country
from matcher.server.main.my_elastic import MyElastic


class TestInitCountry:
    def test_get_cities_from_insee(self) -> None:
        result = get_cities_from_insee()['insee_cities']
        assert len(result) == 75
        assert 'La Rochelle' in result

    def test_get_universities_from_mesri(self) -> None:
        result = get_universities_from_mesri()['mesri_universities']
        assert len(result) == 265

    def test_get_names_from_country_fr(self) -> None:
        result = get_names_from_country('fr')
        assert result == {'alpha_2': 'FR', 'alpha_3': 'FRA', 'all_names': ['France', 'French Republic'],
                          'name': 'France'}

    def test_get_names_from_country_bo(self) -> None:
        result = get_names_from_country('bo')
        assert result == {'alpha_2': 'BO', 'alpha_3': 'BOL', 'all_names': ['Bolivia, Plurinational State of',
                                                                           'Plurinational State of Bolivia', 'Bolivia'],
                          'name': 'Bolivia'}

    def test_get_cities_from_wikidata(self) -> None:
        cities = get_cities_from_wikidata()
        assert len(cities) == 178
        assert set(cities['fr'].keys()) == {'all', 'strict', 'en', 'fr', 'es', 'it'}
        assert 'Dunkirk' in cities['fr']['all']
        assert 'Dunkerque' in cities['fr']['all']
        assert 'Dunkirk' in cities['fr']['en']
        assert 'Dunkirk' not in cities['fr']['fr']
        assert 'Dunkerque' in cities['fr']['fr']
        assert 'Dunkerque' not in cities['fr']['en']

    def test_get_universities_from_wikidata(self) -> None:
        universities = get_universities_from_wikidata()
        assert len(universities) == 216
        assert set(universities['fr'].keys()) == {'all', 'en', 'fr', 'es', 'it'}
        assert 'École normale supérieure de Fontenay-Saint-Cloud' in universities['fr']['all']
        assert 'École normale supérieure de Fontenay-Saint-Cloud' in universities['fr']['en']
        assert 'École normale supérieure de Fontenay-Saint-Cloud' in universities['fr']['fr']
        assert 'Lille Catholic University' in universities['fr']['all']
        assert 'Lille Catholic University' in universities['fr']['en']
        assert 'Lille Catholic University' not in universities['fr']['fr']
        assert 'université catholique de Lille' in universities['fr']['all']
        assert 'université catholique de Lille' in universities['fr']['fr']
        assert 'université catholique de Lille' not in universities['fr']['en']

    def test_get_get_hospitals_from_wikidata(self) -> None:
        hospitals = get_hospitals_from_wikidata()
        assert len(hospitals) == 204
        assert set(hospitals['fr'].keys()) == {'all', 'en', 'fr', 'es', 'it'}
        assert 'Paul Morel Hospital' in hospitals['fr']['all']
        assert 'Paul Morel Hospital' in hospitals['fr']['en']
        assert 'Paul Morel Hospital' not in hospitals['fr']['fr']
        assert 'hôpital Paul-Morel' in hospitals['fr']['fr']
        assert 'hôpital Paul-Morel' not in hospitals['fr']['en']

    @pytest.fixture(scope='class')
    def setup(self) -> None:
        index = 'country-test'
        es = MyElastic()
        yield {'es': es, 'index': index}
        es.delete_index(index=index)

    def test_init_country(self, setup, requests_mock) -> None:
        requests_mock.real_http = True
        requests_mock.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql',
                          json={'results': {'bindings': [
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_01'}},
                              {'country_alpha2': {'value': 'de'}, 'label_native': {'value': 'value_02'}},
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'value_03'}}
                          ]}})
        index = setup['index']
        es = setup['es']
        init_country(index=index)
        all_results = es.count(index=index)
        assert all_results['count'] == 249
        french_results = es.search(index=index, body={'query': {'match': {'alpha_2': 'fr'}}})
        assert french_results['hits']['total']['value'] == 1
        french_result = french_results['hits']['hits'][0]['_source']
        assert french_result['alpha_2'] == 'FR'
        assert french_result['alpha_3'] == 'FRA'
        assert len(french_result['all_names']) == 2
        assert len(french_result['wikidata_cities']) == 2
        assert len(french_result['wikidata_hospitals']) == 2
        assert len(french_result['wikidata_universities']) == 2
        assert len(french_result['stop_words']) == 0
        es.delete_index(index=index)
