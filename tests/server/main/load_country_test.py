import pytest

from matcher.server.main.load_country import get_names_from_country, load_country
from matcher.server.main.my_elastic import MyElastic


class TestLoadCountry:
    def test_get_names_from_country_fr(self) -> None:
        result = get_names_from_country('fr')
        assert result == {'alpha_2': 'FR', 'alpha_3': 'FRA', 'all_names': ['France', 'French Republic'],
                          'name': 'France'}

    def test_get_names_from_country_bo(self) -> None:
        result = get_names_from_country('bo')
        assert result == {'alpha_2': 'BO', 'alpha_3': 'BOL', 'all_names': ['Bolivia, Plurinational State of',
                                                                           'Plurinational State of Bolivia', 'Bolivia'],
                          'name': 'Bolivia'}

    @pytest.fixture(scope='class')
    def setup(self) -> None:
        index = 'country-test'
        es = MyElastic()
        yield {'es': es, 'index': index}
        es.delete_index(index=index)

    def test_load_country(self, setup) -> None:
        index = setup['index']
        es = setup['es']
        load_country(index=index)
        all_results = es.count(index=index)
        assert all_results['count'] == 249
        french_results = es.search(index=index, body={'query': {'match': {'alpha_2': 'fr'}}})
        assert french_results['hits']['total']['value'] == 1
        french_result = french_results['hits']['hits'][0]['_source']
        assert french_result['alpha_2'] == 'FR'
        assert french_result['alpha_3'] == 'FRA'
        assert len(french_result['all_names']) == 2
        es.delete_index(index=index)
