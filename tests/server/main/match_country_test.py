import pytest
import re

from elasticsearch import Elasticsearch
from matcher.server.main.config import config
from matcher.server.main.match_country import construct_keywords_regex, get_countries_from_query


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = 'country-test'
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    es.indices.create(index=index, ignore=[400])
    yield {'es': es, 'index': index}
    es.indices.delete(index=index, ignore=[404])


class TestMatchCountry:
    def test_construct_keywords_regex_with_one_keyword(self, elasticsearch) -> None:
        body = {
            'category': 'keyword',
            'country': 'fr',
            'regex': 'term_01'
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        regex = construct_keywords_regex(elasticsearch['es'], elasticsearch['index'], 'fr')
        assert regex == re.compile('(?<![a-z])term_01(?![a-z])')
        elasticsearch['es'].delete_by_query(index=elasticsearch['index'], body={"query": {"match_all": {}}})

    def test_construct_keywords_regex_with_two_keywords(self, elasticsearch) -> None:
        body = {
            'category': 'keyword',
            'country': 'fr',
            'regex': 'term_02'
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        body = {
            'category': 'keyword',
            'country': 'fr',
            'regex': 'term_03'
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        regex = construct_keywords_regex(elasticsearch['es'], elasticsearch['index'], 'fr')
        assert regex == re.compile('(?<![a-z])term_02(?![a-z])|(?<![a-z])term_03(?![a-z])')
        elasticsearch['es'].delete_by_query(index=elasticsearch['index'], body={"query": {"match_all": {}}})

    @pytest.mark.parametrize(
        'query,expected_country', [
        ('Tour Mirabeau Paris', ['FR']),
        ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', ['FR']),
        ('N\'importe quoi', []),
        ('Sorbonne Université, INSERM, UMRS 1142 LIMICS, Paris, France, APHP.Sorbonne, Fetal Medicine Department, '
         'Armand Trousseau Hospital, Paris, France.', ['FR']),
        ('Hotel-Dieu de France University Hospital, Faculty of Medicine, Saint Joseph University, Beirut, Lebanon.', ['LB'])
    ])
    def test_get_countries_from_query(self, query, expected_country) -> None:
        matched_country = get_countries_from_query(query)
        assert matched_country == expected_country
