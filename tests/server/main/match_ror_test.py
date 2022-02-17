import pytest

from matcher.server.main.load_ror import load_ror
from matcher.server.main.match_ror import match_ror
from matcher.server.main.metrics import compute_precision_recall
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    es = MyElastic()
    load_ror(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix, 'es': es}
    es.delete_index(index=f'{index_prefix}*')


class TestMatchRor:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            ('institut pasteur shanghai', [[['ror_name']]], ['0495fxg12'], '')
        ]
    )
    def test_match_ror(self, elasticsearch, query, strategies, expected_results, expected_logs) -> None:
        args = {'index_prefix': elasticsearch['index_prefix'], 'verbose': True, 'strategies': strategies,
                'query': query}
        response = match_ror(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self, elasticsearch) -> None:
        precision_recall = compute_precision_recall(match_type='ror', index_prefix=elasticsearch['index_prefix'])
        assert precision_recall['precision'] >= 0.81
        assert precision_recall['recall'] >= 0.16
