import pytest

from matcher.server.main.init_grid import init_grid
from matcher.server.main.match_country import get_countries_from_query
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    es = MyElastic()
    yield
    es.delete_index(index='test_grid_cities')
    es.delete_index(index='test_grid_institutions')
    es.delete_index(index='test_grid_institutions_acronyms')


class TestMatchCountry:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            # Query with no meaningful should return no country
            ('Not meaningful string', [['test_grid_cities']], [], 'No results'),
            # Simple query with a city should match the associated country
            ('Tour Mirabeau Paris', [['test_grid_cities']], ['ca', 'fr', 'us'], 'test_grid_cities'),
            # Complex query with a city should match the associated country
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', [['test_grid_cities']],
             ['fr'], 'test_grid_cities'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.', [['test_grid_cities']],
             ['lb', 'us'], 'test_grid_cities'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.',
             [['test_grid_cities', 'test_grid_institutions']], [], 'No results'),
            # Even if city is not unknown, the university name should match the associated country
            ('Université de technologie de Troyes', [['test_grid_institutions']], ['fr'], 'test_grid_institutions')
        ])
    def test_get_countries_from_query(self, elasticsearch, query, strategies, expected_results,
                                      expected_logs) -> None:
        init_grid(index_prefix='test_')
        response = get_countries_from_query(query=query, strategies=strategies)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']
