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
        (['cities'], [['city_01']], True, re.compile('(?<![a-z])city 01(?![a-z])', re.IGNORECASE)),
        (['cities'], [['city_01', 'city_02']], True, re.compile('(?<![a-z])city 01(?![a-z])|(?<![a-z])city 02(?![a-z])',
                                                                re.IGNORECASE)),
        (['cities', 'info'], [['city_01'], ['info_01']], True,
         re.compile('(?<![a-z])city 01(?![a-z])|(?<![a-z])info 01(?![a-z])', re.IGNORECASE)),
        (['universities'], [['université']], True, re.compile('(?<![a-z])universite(?![a-z])', re.IGNORECASE)),
        (['stop_words'], [['word_01', 'word_02']], False, re.compile('word 01|word 02', re.IGNORECASE))
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
        'query,strategies,expected_country', [
            # Query with no meaningful should return no country
            ('Not meaningful string', ['cities', 'info', 'universities'], []),
            # Simple query with a city should match the associated country
            ('Tour Mirabeau Paris', ['cities'], ['fr']),
            # Complex query with a city should match the associated country
            ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', ['cities'], ['fr']),
            # Even if city is not recognized, the university name should match the associated country
            ('Université de technologie de Troyes', ['cities'], []),
            ('Université de technologie de Troyes', ['universities'], ['fr']),
            # With stop words, a misleading hospital name should not match the country
            ('Hotel-Dieu de France University Hospital, Faculty of Medicine, Saint Joseph University, Beirut, Lebanon.',
             ['info'], ['lb'])
        ])
    def test_get_countries_from_query(self, query, strategies, expected_country) -> None:
        matched_country = get_countries_from_query(query, strategies)
        assert matched_country == expected_country
