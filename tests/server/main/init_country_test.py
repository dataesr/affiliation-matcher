from matcher.server.main.init_country import get_cities_from_insee, get_cities_from_wikidata, \
    get_universities_from_mesri, get_universities_from_wikidata, get_info_from_country, get_stop_words_from_country, \
    get_hospitals_from_wikidata, init_country
from matcher.server.main.my_elastic import MyElastic


class TestInitCountry:
    def test_get_cities_from_insee(self) -> None:
        result = get_cities_from_insee()['insee_cities']
        assert len(result) == 75
        assert 'La Rochelle' in result

    def test_get_universities_from_mesri(self) -> None:
        result = get_universities_from_mesri()['mesri_universities']
        assert len(result) == 265

    def test_get_info_from_country_fr(self) -> None:
        result = get_info_from_country('fr')
        assert result == {'alpha_2': 'FR', 'alpha_3': 'FRA', 'info': ['France', 'French Republic']}

    def test_get_info_from_country_bo(self) -> None:
        result = get_info_from_country('bo')
        assert result == {'alpha_2': 'BO', 'alpha_3': 'BOL', 'info': ['Bolivia, Plurinational State of',
                                                                      'Plurinational State of Bolivia', 'Bolivia']}

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

    def test_get_stop_words_from_country_fr(self) -> None:
        french_stop_words = get_stop_words_from_country('fr')['stop_words']
        assert len(french_stop_words) == 0

    def test_get_stop_words_from_country_cn(self) -> None:
        chinese_stop_words = get_stop_words_from_country('cn')['stop_words']
        assert len(chinese_stop_words) == 0

    def test_init_country(self) -> None:
        init_country()
        es = MyElastic()
        all_results = es.search(index='country')
        assert all_results['hits']['total']['value'] == 34
        french_results = es.search(index='country', body={'query': {'match': {'alpha_2': 'fr'}}})
        assert french_results['hits']['total']['value'] == 1
        french_result = french_results['hits']['hits'][0]['_source']
        assert french_result['alpha_2'] == 'FR'
        assert french_result['alpha_3'] == 'FRA'
        assert len(french_result['info']) == 2
        assert len(french_result['wikidata_cities']) == 127
        assert len(french_result['wikidata_universities']) == 1614
        assert len(french_result['stop_words']) == 0
        es.delete_index(index='country')
