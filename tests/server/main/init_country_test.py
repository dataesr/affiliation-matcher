from matcher.server.main.init_country import get_all_cities, get_all_universities, get_info_from_country, \
    get_stop_words_from_country, init_country
from matcher.server.main.my_elastic import MyElastic


class TestInitCountry:
    def test_get_info_from_country_fr(self):
        result = get_info_from_country('fr')
        assert result == {'alpha_2': 'FR', 'alpha_3': 'FRA', 'info': ['France', 'French Republic']}

    def test_get_info_from_country_bo(self):
        result = get_info_from_country('bo')
        assert result == {'alpha_2': 'BO', 'alpha_3': 'BOL', 'info': ['Bolivia, Plurinational State of',
                                                                      'Plurinational State of Bolivia', 'Bolivia']}

    def test_get_all_cities(self):
        cities = get_all_cities()
        assert len(cities) == 177
        assert set(cities['fr'].keys()) == {'all', 'strict', 'en', 'fr', 'es', 'it'}
        assert 'Dunkirk' in cities['fr']['all']
        assert 'Dunkerque' in cities['fr']['all']
        assert 'Dunkirk' in cities['fr']['en']
        assert 'Dunkirk' not in cities['fr']['fr']
        assert 'Dunkerque' in cities['fr']['fr']
        assert 'Dunkerque' not in cities['fr']['en']

    def test_get_universities_from_country_fr(self):
        universities = get_all_universities()
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

    def test_get_stop_words_from_country_fr(self):
        french_stop_words = get_stop_words_from_country('fr')['stop_words']
        assert len(french_stop_words) == 16
        assert 'paris.*tx' in french_stop_words

    def test_get_stop_words_from_country_cn(self):
        chinese_stop_words = get_stop_words_from_country('cn')['stop_words']
        assert len(chinese_stop_words) == 0

    def test_init_country(self):
        es = MyElastic()
        init_country()
        all_results = es.search(index='country', body={'query': {'match_all': {}}})
        assert all_results['hits']['total']['value'] == 249
        french_results = es.search(index='country', body={'query': {'match': {'alpha_2': 'fr'}}})
        assert french_results['hits']['total']['value'] == 1
        french_result = french_results['hits']['hits'][0]['_source']
        assert len(french_result['cities']) == 130
        assert french_result['alpha_2'] == 'FR'
        assert french_result['alpha_3'] == 'FRA'
        assert len(french_result['info']) == 2
        assert len(french_result['stop_words']) == 16
        assert len(french_result['universities']) == 1611
        es.delete_index(index='country')
