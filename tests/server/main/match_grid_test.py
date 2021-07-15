import pytest

from matcher.server.main.load_grid import load_grid
from matcher.server.main.match_grid import match_grid
from matcher.server.main.metrics import compute_precision_recall
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    es = MyElastic()
    load_grid(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix}
    es.delete_index(index=f'{index_prefix}*')


class TestMatchGrid:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            ('institut pasteur shanghai', [['grid_name']], ['grid.428999.7'],
             'Strategy has 1 possibilities that match all criteria')
        ])
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
        assert precision_recall['precision'] >= 0.80
        assert precision_recall['recall'] >= 0.56
