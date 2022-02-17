import pytest

from matcher.server.main.load_grid import load_grid
from matcher.server.main.match_grid import get_ancestors, match_grid, remove_ancestors
from matcher.server.main.metrics import compute_precision_recall
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    es = MyElastic()
    load_grid(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix, 'es': es}
    es.delete_index(index=f'{index_prefix}*')


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
        'query,strategies,expected_results,expected_logs', [
            ('institut pasteur shanghai', [[['grid_name']]], ['grid.429007.8'], '')
        ]
    )
    def test_match_grid(self, elasticsearch, query, strategies, expected_results, expected_logs) -> None:
        args = {'index_prefix': elasticsearch['index_prefix'], 'verbose': True, 'strategies': strategies,
                'query': query}
        response = match_grid(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self, elasticsearch) -> None:
        precision_recall = compute_precision_recall(match_type='grid', index_prefix=elasticsearch['index_prefix'])
        assert precision_recall['precision'] >= 0.87
        assert precision_recall['recall'] >= 0.24
