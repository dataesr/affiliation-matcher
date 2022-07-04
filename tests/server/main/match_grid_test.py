import pytest

from project.server.main.load_grid import load_grid
from project.server.main.load_ror import load_ror
from project.server.main.match_grid import get_ancestors, match_grid, remove_ancestors
from project.server.main.metrics import compute_precision_recall
from project.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    es = MyElastic()
    load_grid(index_prefix=index_prefix)
    load_ror(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix, 'es': es}
    es.delete_index(index=f'{index_prefix}_grid_*')
    es.delete_index(index=f'{index_prefix}_ror_*')


class TestMatchGrid:
    @pytest.mark.parametrize(
        'grid,expected_ancestors', [
            ('grid.489990.5', ['grid.416125.5']),
            ('grid.483522.a', ['grid.457014.3', 'grid.4444.0', 'grid.7902.c'])
        ]
    )
    def test_get_ancestors(self, elasticsearch, grid, expected_ancestors) -> None:
        ancestors = get_ancestors(query=grid, es=elasticsearch['es'], index_prefix=elasticsearch['index_prefix'])
        ancestors.sort()
        expected_ancestors.sort()
        assert ancestors == expected_ancestors

    def test_remove_ancestors(self, elasticsearch):
        grids = remove_ancestors(grids=['grid.489990.5', 'grid.416125.5'], es=elasticsearch['es'],
                                 index_prefix=elasticsearch['index_prefix'])
        grids.sort()
        assert grids == ['grid.489990.5']

    @pytest.mark.parametrize(
        'query,strategies,expected_results', [
            ('université de rennes 2', [[['grid_name']]], ['grid.11619.3e']),
            ('université de paris sorbonne', [[['grid_name']]], ['grid.462844.8']),
            ('mcgill university montreal quebec', [[['grid_name', 'grid_city']],
             [['grid_name', 'grid_cities_by_region']]], ['grid.14709.3b']),
            ('institut pasteur shanghai', [[['grid_name']]], ['grid.429007.8']),
            ('Semmelweis University Budapest Hungary', [[['grid_name', 'grid_city', 'grid_country']]],
             ['grid.11804.3c']),
            ('02feahw73', [[['ror_id']]], ['grid.4444.0']),
            ('grid.4444.0', [[['grid_id']]], ['grid.4444.0'])
        ]
    )
    def test_match_grid(self, elasticsearch, query, strategies, expected_results) -> None:
        args = {'index_prefix': elasticsearch['index_prefix'], 'verbose': True, 'strategies': strategies,
                'query': query}
        response = match_grid(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results

    def test_precision_recall(self, elasticsearch) -> None:
        precision_recall = compute_precision_recall(match_type='grid', index_prefix=elasticsearch['index_prefix'])
        assert precision_recall['precision'] >= 0.88
        assert precision_recall['recall'] >= 0.25
