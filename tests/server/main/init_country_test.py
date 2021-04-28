from elasticsearch import Elasticsearch
from matcher.server.main.config import config
from matcher.server.main.init_country import get_cities_from_country, get_info_from_country, \
    get_stop_words_from_country, get_universities_from_country, init_country


class TestInitCountry:
    def test_get_info_from_country(self):
        result = get_info_from_country('fr')
        assert result == {'alpha_2': 'FR', 'alpha_3': 'FRA', 'info': ['France', 'French']}

    def test_get_cities_from_country_fr(self):
        french_cities = get_cities_from_country('fr')['cities']
        assert len(french_cities) == 75
        assert 'paris' in french_cities
        assert 'nancy' in french_cities
        assert 'issy-les-moulineaux' in french_cities

    def test_get_cities_from_country_cn(self):
        chinese_cities = get_cities_from_country('cn')['cities']
        assert len(chinese_cities) == 0

    def test_get_universities_from_country_fr(self):
        french_universities = get_universities_from_country('fr')['universities']
        assert len(french_universities) == 333
        assert 'Rennes School of Business' in french_universities

    def test_get_universities_from_country_cn(self):
        chinese_universities = get_universities_from_country('cn')['universities']
        assert len(chinese_universities) == 0

    def test_get_stop_words_from_country_fr(self):
        french_stop_words = get_stop_words_from_country('fr')['stop_words']
        assert len(french_stop_words) == 14
        assert 'paris.*tx' in french_stop_words

    def test_get_stop_words_from_country_cn(self):
        chinese_stop_words = get_stop_words_from_country('cn')['stop_words']
        assert len(chinese_stop_words) == 0

    def test_init_country(self):
        es = Elasticsearch(config['ELASTICSEARCH_HOST'])
        init_country()
        all_results = es.search(index='country', body={'query': {'match_all': {}}})
        assert all_results['hits']['total']['value'] == 249
        french_results = es.search(index='country', body={'query': {'ids': {'values': ['fr']}}})
        assert french_results['hits']['total']['value'] == 1
        french_result = french_results['hits']['hits'][0]['_source']
        assert len(french_result['cities']) == 75
        assert french_result['alpha_2'] == 'FR'
        assert french_result['alpha_3'] == 'FRA'
        assert len(french_result['info']) == 2
        assert len(french_result['stop_words']) == 14
        assert len(french_result['universities']) == 333
