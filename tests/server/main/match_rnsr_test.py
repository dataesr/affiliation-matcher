import pytest

from project.server.main.match_rnsr import *


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = config['ELASTICSEARCH_INDEX']
    index_01 = 'index-rnsr-test'
    index_02 = 'index-rnsr-test2'
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    if not es.indices.exists(index):
        es.indices.create(index, ignore=400)
    if not es.indices.exists(index_01):
        es.indices.create(index_01, ignore=400)
    if not es.indices.exists(index_02):
        es.indices.create(index_02, ignore=400)
    yield {'es': es, 'index': index, 'index_01': index_01, 'index_02': index_02}
    if es.indices.exists(index):
        es.indices.delete(index=index)
    if es.indices.exists(index_01):
        es.indices.delete(index=index_01)
    if es.indices.exists(index_02):
        es.indices.delete(index=index_02)


class TestMatchUnstructured:
    @pytest.fixture
    def setup(self, mocker) -> None:
        def mock_match_structured(matching_info, strategies, logs) -> dict:
            return {'matching_info': matching_info, 'strategies': strategies, 'logs': logs}

        mocker.patch('project.server.main.match_rnsr.match_structured', side_effect=mock_match_structured)

    def test_match_unstructured(self, setup) -> None:
        query = 'Biologie et Génétique des interactions Plantes-parasites pour la Protection Intégrée UMR385'
        result = match_unstructured(2019, query)

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
        'param_year,param_query,param_fields,param_size,expected_ids_length,expected_highlights_length', [
            ('test', 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 3, 3),
            ('test2', 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 4, 2),
            (2019, 'Plate-Forme', ['names'], 200, 21, 21),
            (2019, 'PF-CCB', ['acronyms'], 200, 1, 1),
            (2019, 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 1, 1, 1)
        ])
    def test_get_info_by_names(self, elasticsearch, param_year, param_query, param_fields, param_size,
                               expected_ids_length, expected_highlights_length) -> None:
        body = {'id': '12', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-01']}
        elasticsearch['es'].index(elasticsearch['index_01'], body=body, refresh=True)
        body = {'id': '13', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-02']}
        elasticsearch['es'].index(elasticsearch['index_01'], body=body, refresh=True)
        body = {'id': '14', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2019-03']}
        elasticsearch['es'].index(elasticsearch['index_01'], body=body, refresh=True)
        body = {'id': '15', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2017-01']}
        elasticsearch['es'].index(elasticsearch['index_02'], body=body, refresh=True)
        body = {'id': '16', 'names': ['Plate-Forme de Criblage chémogénomique et biologique 2017-02']}
        elasticsearch['es'].index(elasticsearch['index_02'], body=body, refresh=True)
        result = get_info(param_year, param_query, param_fields, param_size, False, param_fields)
        assert len(result.get('ids')) == expected_ids_length
        assert len(result.get('highlights')) == expected_highlights_length
        assert len(result.get('nb_matches')) == expected_highlights_length

    @pytest.mark.parametrize('param_year,param_query,param_fields,param_size,expected_results_length', [
        ('test', 'PF-CCB', ['acronyms'], 200, 1),
    ])
    def test_get_info_by_acronyms(self, elasticsearch, param_year, param_query, param_fields, param_size,
                                  expected_results_length) -> None:
        body = {'id': '112', 'acronyms': ['PF-CCB']}
        elasticsearch['es'].index(elasticsearch['index_01'], body=body, refresh=True)
        result = get_info(param_year, param_query, param_fields, param_size, False, param_fields)
        assert len(result.get('ids')) == expected_results_length
        assert len(result.get('highlights')) == expected_results_length
        assert len(result.get('nb_matches')) == expected_results_length


class TestGetMatch:
    @pytest.fixture
    def setup(self, mocker) -> None:
        def mock_get_info(year, query, search_fields, size, verbose, highlights, fuzzy_ok=False) -> dict:
            return {'year': year, 'query': query, 'search_fields': search_fields, 'size': size,
                    'verbose': verbose, 'highlights': highlights, 'fuzzy_ok': fuzzy_ok}

        mocker.patch('project.server.main.match_rnsr.get_info', side_effect=mock_get_info)

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_code(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['code_numbers']
        assert result.get('size') == 20
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['code_numbers']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_label(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_code_label(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['code_numbers.labels']
        assert result.get('size') == 10000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['code_numbers.labels']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_digit(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_code_digit(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['code_numbers.digits']
        assert result.get('size') == 20
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['code_numbers.digits']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_fuzzy(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_code_fuzzy(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['code_numbers', 'code_numbers.digits']
        assert result.get('size') == 1000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['code_numbers', 'code_numbers.digits']
        assert result.get('fuzzy_ok') is True

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_city(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_city(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['addresses']
        assert result.get('size') == 5000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['addresses']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_name(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_name(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['names']
        assert result.get('size') == 200
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['names']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_acronym(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['acronyms']
        assert result.get('size') == 5000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['acronyms']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_name(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_supervisors_name(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['supervisors_name']
        assert result.get('size') == 10000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['supervisors_name']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_id(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_supervisors_id(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['supervisors_id']
        assert result.get('size') == 2000
        assert result.get('verbose') is param_verbose
        assert result.get('highlights') == ['supervisors_id']
        assert result.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        result = get_match_supervisors_acronym(param_year, param_query, param_verbose)
        assert result.get('year') == param_year
        assert result.get('query') == param_query
        assert result.get('search_fields') == ['supervisors_acronym']
        assert result.get('size') == 2000
        assert result.get('verbose') is param_verbose
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
