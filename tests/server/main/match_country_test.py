import pytest

from project.server.main.load_country import load_country
from project.server.main.load_grid import load_grid
from project.server.main.load_rnsr import load_rnsr
from project.server.main.load_ror import load_ror
from project.server.main.match_country import match_country, COUNTRY_DEFAULT_STRATEGIES
from project.server.main.metrics import compute_precision_recall
from project.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    load_country(index_prefix=index_prefix)
    load_grid(index_prefix=index_prefix)
    load_rnsr(index_prefix=index_prefix)
    load_ror(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix}
    es = MyElastic()
    es.delete_index(index=f'{index_prefix}_country_*')
    es.delete_index(index=f'{index_prefix}_grid_*')
    es.delete_index(index=f'{index_prefix}_rnsr_*')
    es.delete_index(index=f'{index_prefix}_ror_*')


class TestMatchCountry:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            # Query with no meaningful should return no country
            ('Not meaningful string', [[['grid_city']]], [], 'No results'),
            # Vague french affiliation,
            ('UMR CNRS', [[['rnsr_code_prefix', 'rnsr_supervisor_acronym']]], ['fr'], 'strategy'),
            # RoR id,
            ('02feahw73', [[['ror_id']]], ['fr'], 'strategy'),
            # grid id,
            ('grid.4444.0', [[['grid_id']]], ['fr'], 'strategy'),
            # Simple query with a city should match the associated countries
            ('Tour Mirabeau Paris', [[['grid_city']]], ['ca', 'fr', 'us'], 'grid_city'),
            # Complex query with a city should match the associated country
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', [[['grid_city']]],
             ['fr'], 'grid_city'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.', [[['grid_city']]],
             ['lb', 'us'], 'grid_city'),
            ('Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon.',
             [[['grid_city', 'grid_name', 'country_name']]], ['lb'], 'strategy'),
            ('University Nottingham, Chair, Nomenclature and Standards Committee International Union Basic Clinical Pharmacology (NC-IUPHAR)',
             [[['grid_name', 'grid_cities_by_region']]], ['gb'], 'strategy'),
            # Even if city is not unknown, the university name should match the associated country
            ('Université de technologie de Troyes', [[['grid_name']]], ['fr'], 'grid_name'),
            # ('saint louis', COUNTRY_DEFAULT_STRATEGIES, [], 'No results'),
            # ('MN orleans', COUNTRY_DEFAULT_STRATEGIES, [], 'No results'),
            # ('Ltd Novel', COUNTRY_DEFAULT_STRATEGIES, [], 'No results'),
            # ('Public Health Chan', COUNTRY_DEFAULT_STRATEGIES, [], 'No results'),
            # ('Hotel Dieu de France Beirut Liban', COUNTRY_DEFAULT_STRATEGIES, ['lb'], 'strategy liban')
        ])
    def test_get_countries_from_query(self, elasticsearch, query, strategies, expected_results,
                                      expected_logs) -> None:
        args = {'index_prefix': elasticsearch['index_prefix'], 'verbose': True, 'strategies': strategies,
                'query': query}
        response = match_country(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self, elasticsearch):
        precision_recall = compute_precision_recall(match_type='country', index_prefix=elasticsearch['index_prefix'])
        assert precision_recall['precision'] >= 0.89
        assert precision_recall['recall'] >= 0.52
