import pytest

from project.server.main.match_rnsr import *


class TestMatchUnstructured:
    def test_1(self) -> None:
        res = match_unstructured(2015, "INS1640 INSHS Institut des Sciences Humaines et Sociales ORLEANS")
        assert res.get('match') is None

    def test_2(self) -> None:
        res = match_unstructured(2015, "MOY1000  Délégation Alsace STRASBOURG")
        assert res.get('match') is None


class TestMatchFields:
    def test_3(self) -> None:
        res = match_fields(2018, "UMR 5223", "INGENIERIE DES MATERIAUX POLYMERES", "VILLEURBANNE CEDEX", "IMP",
                           "196917744")
        assert res.get('match') == '200711890Y'

    @pytest.mark.skip
    def test_4(self) -> None:
        res = match_fields(2019, None, "BUREAU DE RECHERCHES GEOLOGIQUES ET MINIERES", "ORLEANS", "BRGM", "582056149")
        assert res.get('match') == '195922846R'


@pytest.mark.parametrize("param_year,param_query,param_fields,param_size,expected_results_length", [
    (2019, "Plate-Forme de Criblage chémogénomique et biologique", ["names"], 200, 3),
    (2017, "Plate-Forme de Criblage chémogénomique et biologique", ["names"], 200, 2),
    (2019, "Plate-Forme", ["names"], 200, 21),
    (2019, "PF-CCB", ["acronyms"], 200, 1),
    (2019, "Plate-Forme de Criblage chémogénomique et biologique", ["names"], 1, 1)
])
def test_get_info_by_acronym(param_year, param_query, param_fields, param_size, expected_results_length) -> None:
    results = get_info(param_year, param_query, param_fields, param_size, False, param_fields)
    assert len(results.get('ids')) == expected_results_length
    assert len(results.get('highlights')) == expected_results_length
    assert len(results.get('nb_matches')) == expected_results_length


class TestGetMatch:
    @pytest.fixture
    def setup(self, mocker) -> None:
        def mock_get_info(year, query, search_fields, size, verbose, highlights, fuzzy_ok=False) -> dict:
            return {"year": year, "query": query, "search_fields": search_fields, "size": size,
                    "verbose": verbose, "highlights": highlights, "fuzzy_ok": fuzzy_ok}

        mocker.patch("project.server.main.match_rnsr.get_info", side_effect=mock_get_info)

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["code_numbers"]
        assert info.get("size") == 20
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_label(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_label(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["code_numbers.labels"]
        assert info.get("size") == 10000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers.labels"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_digit(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_digit(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["code_numbers.digits"]
        assert info.get("size") == 20
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers.digits"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_fuzzy(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_code_fuzzy(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["code_numbers", "code_numbers.digits"]
        assert info.get("size") == 1000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers", "code_numbers.digits"]
        assert info.get("fuzzy_ok") is True

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_city(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_city(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["addresses"]
        assert info.get("size") == 5000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["addresses"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_name(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_name(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["names"]
        assert info.get("size") == 200
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["names"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_acronym(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["acronyms"]
        assert info.get("size") == 5000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["acronyms"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_name(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_name(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["supervisors_name"]
        assert info.get("size") == 10000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_name"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_id(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_id(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["supervisors_id"]
        assert info.get("size") == 2000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_id"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_query,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_acronym(self, setup, param_year, param_query, param_verbose) -> None:
        info = get_match_supervisors_acronym(param_year, param_query, param_verbose)
        assert info.get("year") == param_year
        assert info.get("query") == param_query
        assert info.get("search_fields") == ["supervisors_acronym"]
        assert info.get("size") == 2000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_acronym"]
        assert info.get("fuzzy_ok") is False
