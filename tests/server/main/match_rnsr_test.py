import pytest

from project.server.main.load_rnsr import load_rnsr
from project.server.main.match_rnsr import match_rnsr
from project.server.main.metrics import compute_precision_recall
from project.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index_prefix = 'test'
    es = MyElastic()
    load_rnsr(index_prefix=index_prefix)
    yield {'index_prefix': index_prefix}
    es.delete_index(index=f'{index_prefix}_rnsr_*')


class TestMatchRnsr:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            ('Laboratoire de planétologie de Grenoble', [[['rnsr_name']]], ['199911794D'],
             'Equivalent strategies have 1 possibilities that match one of the strategy')
        ])
    def test_match_rnsr(self, elasticsearch, query, strategies, expected_results, expected_logs) -> None:
        args = {'index_prefix': elasticsearch['index_prefix'], 'verbose': True, 'strategies': strategies,
                'query': query}
        response = match_rnsr(conditions=args)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self, elasticsearch) -> None:
        precision_recall = compute_precision_recall(match_type='rnsr', index_prefix=elasticsearch['index_prefix'])
        assert precision_recall['precision'] >= 0.96
        assert precision_recall['recall'] >= 0.81
