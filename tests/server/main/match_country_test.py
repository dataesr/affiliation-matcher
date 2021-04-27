import pytest
import re

from elasticsearch import Elasticsearch
from matcher.server.main.config import config
from matcher.server.main.match_country import get_countries_from_query, get_regex_from_country_by_fields


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = 'country-test'
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    es.indices.create(index=index, ignore=[400])
    yield {'es': es, 'index': index}
    es.indices.delete(index=index, ignore=[404])


class TestMatchCountry:
    @pytest.mark.parametrize('fields,values,is_complex,expected_regex', [
        (['cities'], [['city_01']], True, re.compile('(?<![a-z])city_01(?![a-z])', re.IGNORECASE)),
        (['cities'], [['city_01', 'city_02']], True, re.compile('(?<![a-z])city_01(?![a-z])|(?<![a-z])city_02(?![a-z])', re.IGNORECASE)),
        (['cities', 'info'], [['city_01'], ['info_01']], True, re.compile('(?<![a-z])city_01(?![a-z])|(?<![a-z])info_01(?![a-z])', re.IGNORECASE)),
        (['stop_words'], [['word_01', 'word_02']], False, re.compile('word_01|word_02', re.IGNORECASE))
    ])
    def test_get_regex_from_country_by_fields(self, elasticsearch, fields, values, is_complex, expected_regex) -> None:
        body = {}
        for (field, value) in zip(fields, values):
            body[field] = value
        elasticsearch['es'].index(elasticsearch['index'], id='fr', body=body, refresh=True)
        regex = get_regex_from_country_by_fields(elasticsearch['es'], elasticsearch['index'], 'fr', fields, is_complex)
        assert regex == expected_regex
        elasticsearch['es'].delete_by_query(index=elasticsearch['index'], body={'query': {'match_all': {}}})

    @pytest.mark.parametrize(
        'query,expected_country', [
            ('Tour Mirabeau Paris', ['fr']),
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', ['fr']),
            ('N\'importe quoi', []),
            ('Sorbonne Université, INSERM, UMRS 1142 LIMICS, Paris, France, APHP.Sorbonne, Fetal Medicine Department, '
             'Armand Trousseau Hospital, Paris, France.', ['fr']),
            ('Hotel-Dieu de France University Hospital, Faculty of Medicine, Saint Joseph University, Beirut, Lebanon.',
             ['lb'])
        ])
    def test_get_countries_from_query(self, query, expected_country) -> None:
        matched_country = get_countries_from_query(query)
        assert matched_country == expected_country
