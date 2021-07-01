import pytest

from matcher.server.main.load_country import load_country
from matcher.server.main.load_grid import load_grid
from matcher.server.main.match_country import match_country
from matcher.server.main.metrics import compute_precision_recall
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    es = MyElastic()
    load_grid(index_prefix='test')
    load_country(index_prefix='test')
    yield
    es.delete_index(index='test_grid_*')
    es.delete_index(index='test_country_*')


class TestMatchCountry:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            # Query with no meaningful should return no country
            ('Not meaningful string', [['grid_city']], [], 'No results'),
            # Simple query with a city should match the associated country
            ('Tour Mirabeau Paris', [['grid_city']], ['ca', 'fr', 'us'], 'grid_city'),
            # Complex query with a city should match the associated country
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', [['grid_city']],
             ['fr'], 'grid_city'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.', [['grid_city']],
             ['lb', 'us'], 'grid_city'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.',
             [['grid_city', 'grid_name', 'country_all_names']], ['lb'], 'strategy'),
            # Even if city is not unknown, the university name should match the associated country
            ('Université de technologie de Troyes', [['grid_name']], ['fr'], 'grid_name')
        ])
    def test_get_countries_from_query(self, elasticsearch, query, strategies, expected_results,
                                      expected_logs) -> None:
        args = {'index_prefix': 'test', 'verbose': True, 'strategies': strategies}
        args['query'] = query
        response = match_country(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']
    
    def test_precision_recall(self, elasticsearch):
        precision_recall = compute_precision_recall(match_type='country', index_prefix='test')
        assert precision_recall['precision'] >= 0.97
