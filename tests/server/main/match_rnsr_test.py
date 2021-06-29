import pytest
import requests

from matcher.server.main.load_rnsr import load_rnsr
from matcher.server.main.match_rnsr import match_rnsr
from matcher.server.main.my_elastic import MyElastic

def get_data():
    url = "https://storage.gra.cloud.ovh.net/v1/AUTH_32c5d10cb0fe4519b957064a111717e3/models/match_pubmed_affiliations_with_countries_v3.json"
    data = requests.get(url).json()
    return data

def compute_precision_recall(data):
    nb_TP, nb_FP, nb_FN = 0, 0, 0
    false_positive, false_negative = [], []
    for ix, d in enumerate(data_test):
        if d['rnsr']:
            res = match(d['label'])
            for x in res['results']:
                if x in d['rnsr']:
                    nb_TP += 1
                else:
                    nb_FP += 1
                    false_positive.append(d)
            for x in d['rnsr']:
                if x not in res['results']:
                    nb_FN += 1
                    false_negative.append(d)

    precision = nb_TP / (nb_TP + nb_FP)
    recall = nb_TP / (nb_TP + nb_FN)
    res = {"precision" : precision, "recall" : recall}
    logger.debug(f"Precision and recall for RNSR matcher": {res})
    return res

@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    es = MyElastic()
    load_rnsr(index_prefix='test')
    yield
    es.delete_index(index='test_rnsr_*')

class TestMatchRnsr:
    @pytest.mark.parametrize(
        'query,strategies,expected_results,expected_logs', [
            ('Laboratoire de planétologie de Grenoble', [['test_rnsr_name']], ['199911794D'],
             'Strategy has 1 possibilities that match all criteria')
        ])
    def test_match_rnsr(self, elasticsearch, query, strategies, expected_results, expected_logs) -> None:
        response = match_rnsr(query=query, strategies=strategies)
        results = response['results']
        results.sort()
        assert results == expected_results
        assert expected_logs in response['logs']

    def test_precision_recall(self):
        data = get_data()
        precision_recall = compute_precision_recall(data)
        assert precision_recall['precision'] >= 0.97
        assert precision_recall['recall'] >= 0.75
