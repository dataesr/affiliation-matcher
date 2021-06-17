import pytest

from matcher.server.main.init_country import init_country
from matcher.server.main.match_country import get_countries_from_query, remove_forbidden_countries
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = 'country-test'
    es = MyElastic()
    es.create_index(index=index)
    yield {'es': es, 'index': index}
    es.delete_index(index=index)


class TestMatchCountry:
    def test_remove_forbidden_countries(self):
        countries = [{'alpha_2': 'fr'}, {'alpha_2': 'lb'}]
        query = 'Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.'
        results = remove_forbidden_countries(countries=countries, query=query)
        assert results == [{'alpha_2': 'lb'}]

    @pytest.mark.parametrize(
        'query,strategies,expected_country', [
            # Query with no meaningful should return no country
            ('Not meaningful string', [['wikidata_cities']], []),
            # Simple query with a city should match the associated country
            ('Tour Mirabeau Paris', [['wikidata_cities']], [{'alpha_2': 'fr', 'name': 'France'}]),
            # Complex query with a city should match the associated country
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', [['wikidata_cities']],
             [{'alpha_2': 'fr', 'name': 'France'}]),
            # Country with only alpha_3
            ('St Cloud Hospital, St Cloud, MN, USA.', [['alpha_3']], [{'alpha_2': 'us', 'name': 'United States'}]),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.',
             [['wikidata_cities', 'wikidata_hospitals', 'all_names']], [{'alpha_2': 'lb', 'name': 'Lebanon'}]),
            # Even if city is not unknown, the university name should match the associated country
            ('Université de technologie de Troyes', [['wikidata_universities']], [{'alpha_2': 'fr', 'name': 'France'}])
        ])
    def test_get_countries_from_query(self, elasticsearch, requests_mock, query, strategies, expected_country) -> None:
        requests_mock.real_http = True
        requests_mock.get('https://query.wikidata.org/bigdata/namespace/wdq/sparql',
                          json={'results': {'bindings': [
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'Paris'}},
                              {'country_alpha2': {'value': 'fr'}, 'label_native': {'value': 'Lille'}},
                              {'country_alpha2': {'value': 'lb'}, 'label_native': {'value': 'Beirut'}},
                              {'country_alpha2': {'value': 'fr'}, 'label_native':
                                  {'value': 'Université de technologie de Troyes'}}
                          ]}})
        index = elasticsearch['index']
        init_country(index=index)
        matched_country = get_countries_from_query(query=query, strategies=strategies, index=index)
        assert matched_country == expected_country
