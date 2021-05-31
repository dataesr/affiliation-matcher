import pytest

from matcher.server.main.config import ELASTICSEARCH_INDEX
from matcher.server.main.match_rnsr import match_structured, match_unstructured, get_info, get_match_code, \
    get_match_code_label, get_match_code_digit, get_match_code_fuzzy, get_match_city, get_match_name, \
    get_match_acronym, get_match_supervisors_name, get_match_supervisors_id, get_match_supervisors_acronym, \
    get_supervisors
from matcher.server.main.my_elastic import MyElastic


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = ELASTICSEARCH_INDEX
    index_other = 'index-rnsr-test-other'
    es = MyElastic()
    es.indices.create(index=index, ignore=[400])
    es.indices.create(index=index_other, ignore=[400])
    yield {'es': es, 'index': index, 'index_other': index_other}
    es.indices.delete(index=index, ignore=[404])
    es.indices.delete(index=index_other, ignore=[404])


class TestMatchUnstructured:
    @pytest.fixture
    def setup(self, mocker) -> None:
        def mock_match_structured(matching_info, strategies, logs) -> dict:
            return {'matching_info': matching_info, 'strategies': strategies, 'logs': logs}

        mocker.patch('matcher.server.main.match_rnsr.match_structured', side_effect=mock_match_structured)

    def test_match_unstructured(self, setup, elasticsearch) -> None:
        body = {
            'id': '194517892S',
            'names': ['Biologie et Génétique des interactions Plantes-parasites pour la Protection Intégrée'],
            'code_numbers': ['UMR385'],
            'supervisors_id': [],
            'supervisors_name': [],
            'supervisors_acronym': []
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        query = 'Biologie et Génétique des interactions Plantes-parasites pour la Protection Intégrée UMR385'
        result = match_unstructured(year='test', query=query)

        assert len(result.get('matching_info')) == 9
        assert 'code' in result.get('matching_info')
        assert result.get('matching_info').get('code') == {'highlights': {'194517892S': ['<em>UMR385</em>']},
                                                           'ids': ['194517892S'], 'nb_matches': {'194517892S': 1}}
        assert len(result.get('strategies')) == 24
        assert 'code;name' in result.get('strategies')
        assert result.get('logs') == '<h1> &#128269; {}</h1>'.format(query)


class TestMatchStructured:
    def test_match_structured(self, elasticsearch) -> None:
        id = '194517892S'
        body = {
            'id': id,
            'supervisors_id': [],
            'supervisors_name': [],
            'supervisors_acronym': []
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        matching_info = {
            'code_digit': {'highlights': {id: ['<em>UMR385</em>']}, 'ids': [id], 'nb_matches': {id: 1}},
            'name': {'highlights': {id: ['<em>UMR385</em>']}, 'ids': [id], 'nb_matches': {id: 1}}
        }
        strategies = ['code_digit;name']
        logs = ''
        result = match_structured(matching_info, strategies, logs)
        assert result.get('match') == id
        assert 'Strategie testée : {}'.format(strategies[0]) in result.get('logs')


class TestGetInfo:
    @pytest.mark.parametrize(
        'year,query,fields,size,expected_results_length', [
            ('test', 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 3),
            ('test2', 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 2),
            ('test', 'Plate-Forme', ['names'], 200, 5),
            ('test', 'PF-CCB', ['acronyms'], 200, 1),
            ('test', 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 1, 1)
        ])
    def test_get_info_by_names(self, elasticsearch, year, query, fields, size, expected_results_length) -> None:
        body = {'id': '12', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-01'], 'acronyms':
                'PF-CCB'}
        elasticsearch['es'].index(index=elasticsearch['index'], body=body, refresh=True)
        body = {'id': '13', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-02']}
        elasticsearch['es'].index(index=elasticsearch['index'], body=body, refresh=True)
        body = {'id': '14', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-03']}
        elasticsearch['es'].index(index=elasticsearch['index'], body=body, refresh=True)
        body = {'id': '15', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2017-01']}
        elasticsearch['es'].index(index=elasticsearch['index_other'], body=body, refresh=True)
        body = {'id': '16', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2017-02']}
        elasticsearch['es'].index(index=elasticsearch['index_other'], body=body, refresh=True)
        body = {'id': '17', 'names': ['Plate-Forme']}
        elasticsearch['es'].index(index=elasticsearch['index'], body=body, refresh=True)
        body = {'id': '18', 'names': ['Plate-Forme other']}
        elasticsearch['es'].index(index=elasticsearch['index'], body=body, refresh=True)
        result = get_info(year=year, query=query, search_fields=fields, size=size, highlights=fields)
        assert len(result.get('ids')) == expected_results_length
        assert len(result.get('highlights')) == expected_results_length
        assert len(result.get('nb_matches')) == expected_results_length
        elasticsearch['es'].delete_all_by_query(index=elasticsearch['index'])
        elasticsearch['es'].delete_all_by_query(index=elasticsearch['index_other'])

    @pytest.mark.parametrize('year,query,fields,size,expected_results_length', [
        ('test', 'PF-CCB', ['acronyms'], 200, 1),
    ])
    def test_get_info_by_acronyms(self, elasticsearch, year, query, fields, size, expected_results_length)\
            -> None:
        body = {'id': '112', 'acronyms': ['PF-CCB']}
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        result = get_info(year=year, query=query, search_fields=fields, size=size, highlights=fields)
        assert len(result.get('ids')) == expected_results_length
        assert len(result.get('highlights')) == expected_results_length
        assert len(result.get('nb_matches')) == expected_results_length


class TestGetMatch:
    @pytest.fixture
    def setup(self, mocker) -> None:
        def mock_get_info(year, query, search_fields, size, highlights, fuzzy_ok=False) -> dict:
            return {'year': year, 'query': query, 'search_fields': search_fields, 'size': size,
                    'highlights': highlights, 'fuzzy_ok': fuzzy_ok}

        mocker.patch('matcher.server.main.match_rnsr.get_info', side_effect=mock_get_info)

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_code(self, setup, year, query) -> None:
        result = get_match_code(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['code_numbers']
        assert result.get('size') == 20
        assert result.get('highlights') == ['code_numbers']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test')])
    def test_get_match_code_label(self, setup, year, query) -> None:
        result = get_match_code_label(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['code_numbers.labels']
        assert result.get('size') == 10000
        assert result.get('highlights') == ['code_numbers.labels']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_code_digit(self, setup, year, query) -> None:
        result = get_match_code_digit(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['code_numbers.digits']
        assert result.get('size') == 20
        assert result.get('highlights') == ['code_numbers.digits']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_code_fuzzy(self, setup, year, query) -> None:
        result = get_match_code_fuzzy(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['code_numbers', 'code_numbers.digits']
        assert result.get('size') == 1000
        assert result.get('highlights') == ['code_numbers', 'code_numbers.digits']
        assert result.get('fuzzy_ok') is True

    @pytest.mark.parametrize('year,query', [(42, 'test')])
    def test_get_match_city(self, setup, year, query) -> None:
        result = get_match_city(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['addresses']
        assert result.get('size') == 5000
        assert result.get('highlights') == ['addresses']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_name(self, setup, year, query) -> None:
        result = get_match_name(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['names']
        assert result.get('size') == 200
        assert result.get('highlights') == ['names']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_acronym(self, setup, year, query) -> None:
        result = get_match_acronym(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['acronyms']
        assert result.get('size') == 5000
        assert result.get('highlights') == ['acronyms']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_supervisors_name(self, setup, year, query) -> None:
        result = get_match_supervisors_name(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['supervisors_name']
        assert result.get('size') == 10000
        assert result.get('highlights') == ['supervisors_name']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_supervisors_id(self, setup, year, query) -> None:
        result = get_match_supervisors_id(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['supervisors_id']
        assert result.get('size') == 2000
        assert result.get('highlights') == ['supervisors_id']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('year,query', [(42, 'test'), (42, 'test')])
    def test_get_match_supervisors_acronym(self, setup, year, query) -> None:
        result = get_match_supervisors_acronym(year, query)
        assert result.get('year') == year
        assert result.get('query') == query
        assert result.get('search_fields') == ['supervisors_acronym']
        assert result.get('size') == 2000
        assert result.get('highlights') == ['supervisors_acronym']
        assert result.get('fuzzy_ok') is False


class TestGetSupervisors:
    def test_get_supervisors(self, elasticsearch) -> None:
        id = 42
        supervisors_id = ['id_01', 'id_02']
        supervisors_name = ['name_01', 'name_02', 'name_03']
        supervisors_acronym = ['acronym_01']
        body = {
            'id': id,
            'supervisors_id': supervisors_id,
            'supervisors_name': supervisors_name,
            'supervisors_acronym': supervisors_acronym
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        result = get_supervisors(id)
        assert isinstance(result, dict)
        assert result.get('supervisors_id', None) == supervisors_id
        assert result.get('supervisors_name', None) == supervisors_name
        assert result.get('supervisors_acronym', None) == supervisors_acronym
