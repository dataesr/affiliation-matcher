import pytest
import requests

from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.match_rnsr import match_rnsr
from matcher.server.main.metrics import compute_precision_recall
from matcher.server.main.my_elastic import MyElastic

@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    es = MyElastic()
    load_rnsr(index_prefix='test')
    yield
    es.delete_index(index='test_rnsr_*')

class TestMatchRnsr:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            ('Laboratoire de planétologie de Grenoble', [['rnsr_name']], ['199911794D'],
             'Strategy has 1 possibilities that match all criteria')
        ])
    def test_match_rnsr(self, elasticsearch, query, strategies, expected_results, expected_logs) -> None:
        response = match_rnsr(query=query, strategies=strategies, index_prefix='test')
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self):
        precision_recall = compute_precision_recall(match_type='rnsr', index_prefix='test')
        assert precision_recall['precision'] >= 0.97
        assert precision_recall['recall'] >= 0.75
