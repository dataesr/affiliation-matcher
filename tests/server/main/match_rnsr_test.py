import pytest

from project.server.main.match_rnsr import *


@pytest.fixture(scope='module')
def elasticsearch() -> dict:
    index = config['ELASTICSEARCH_INDEX']
    es = Elasticsearch(config['ELASTICSEARCH_HOST'])
    if not es.indices.exists(index):
        es.indices.create(index, ignore=400)
    yield {'es': es, 'index': index}
    es.indices.delete(index=index)


class TestMatchUnstructured:
    def test_match_unstructured_non_existent(self) -> None:
        result = match_unstructured(2019, 'this is a non-existent data')
        assert result.get('match') is None

    def test_match_unstructured_too_short(self) -> None:
        result = match_unstructured(2019, 'Biologie et Génétique des interactions Plantes-parasites pour la Protection '
                                          'Intégrée')
        assert result.get('match') is None

    def test_match_unstructured(self, elasticsearch) -> None:
        id = '194517892S'
        supervisors_id = ['130002793', '180089013', '331596270', '180070039', '193401312', '130002793']
        supervisors_name = ['Centre de Cooperation Internationale en Recherche Agronomique pour le Developpement',
                            'Montpellier SupAgro',
                            "Montpellier SupAgro - Institut national d'etudes superieures agronomiques de Montpellier",
                            'ENSAM',
                            "Institut national de recherche pour l'agriculture, l'alimentation et l'environnement",
                            'Centre national de la recherche scientifique',
                            'Institut national de la recherche en agronomie',
                            "Montpellier SupAgro - Institut national d'études supérieures agronomiques de Montpellier",
                            'Ecole nationale agronomique Montpellier', 'CNRS', 'CIRAD', 'INRAE', 'INRA']
        supervisors_acronym = ['Montpellier SupAgro', 'ENSAM', 'CNRS', 'CIRAD', 'INRAE', 'INRA']
        body = {
            'id': id,
            'supervisors_id': supervisors_id,
            'supervisors_name': supervisors_name,
            'supervisors_acronym': supervisors_acronym
        }
        elasticsearch['es'].index(elasticsearch['index'], body=body, refresh=True)
        result = match_unstructured(2019, 'Biologie et Génétique des interactions Plantes-parasites pour la Protection '
                                          'Intégrée UMR385')
        assert result.get('match') == id


class TestGetInfo:
    @pytest.mark.parametrize('param_year,param_query,param_fields,param_size,expected_results_length', [
        (2019, 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 3),
        (2017, 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 200, 2),
        (2019, 'Plate-Forme', ['names'], 200, 21),
        (2019, 'PF-CCB', ['acronyms'], 200, 1),
        (2019, 'Plate-Forme de Criblage chémogénomique et biologique', ['names'], 1, 1)
    ])
    def test_get_info_by_acronym(self, param_year, param_query, param_fields, param_size, expected_results_length) -> \
            None:
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
        info = get_match_code(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['code_numbers']
        assert info.get('size') == 20
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['code_numbers']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_label(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_label(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['code_numbers.labels']
        assert info.get('size') == 10000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['code_numbers.labels']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_digit(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_digit(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['code_numbers.digits']
        assert info.get('size') == 20
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['code_numbers.digits']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_code_fuzzy(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_fuzzy(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['code_numbers', 'code_numbers.digits']
        assert info.get('size') == 1000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['code_numbers', 'code_numbers.digits']
        assert info.get('fuzzy_ok') is True

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_city(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_city(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['addresses']
        assert info.get('size') == 5000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['addresses']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_name(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_name(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['names']
        assert info.get('size') == 200
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['names']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_acronym(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['acronyms']
        assert info.get('size') == 5000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['acronyms']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_name(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_name(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['supervisors_name']
        assert info.get('size') == 10000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['supervisors_name']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_id(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_id(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['supervisors_id']
        assert info.get('size') == 2000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['supervisors_id']
        assert info.get('fuzzy_ok') is False

    @pytest.mark.parametrize('param_year,param_query,param_verbose', [(42, 'test', False), (42, 'test', True)])
    def test_get_match_supervisors_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_acronym(param_year, param_query, param_verbose)
        assert info.get('year') == param_year
        assert info.get('query') == param_query
        assert info.get('search_fields') == ['supervisors_acronym']
        assert info.get('size') == 2000
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ['supervisors_acronym']
        assert info.get('fuzzy_ok') is False


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
