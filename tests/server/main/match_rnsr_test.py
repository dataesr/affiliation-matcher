import pytest

from project.server.main.match_rnsr import *


class TestMatchUnstructured:
    def test_1(self):
        res = match_unstructured(2015, "INS1640 INSHS Institut des Sciences Humaines et Sociales ORLEANS")
        assert res.get('match') is None

    def test_2(self):
        res = match_unstructured(2015, "MOY1000  Délégation Alsace STRASBOURG")
        assert res.get('match') is None


class TestMatchFields:
    def test_3(self):
        res = match_fields(2018, "UMR 5223", "INGENIERIE DES MATERIAUX POLYMERES", "VILLEURBANNE CEDEX", "IMP",
                           "196917744")
        assert res.get('match') == '200711890Y'

    def test_4(self):
        res = match_fields(2019, None, "BUREAU DE RECHERCHES GEOLOGIQUES ET MINIERES", "ORLEANS", "BRGM", "582056149")
        assert res.get('match') == '195922846R'


class TestGetInfo:
    def test_get_info_by_acronym(self):
        info = get_info(2019, 'PF-CCB', ['acronyms'], 20, False, ['acronyms'], False)
        assert info.get('ids') == ['000021537K']
        assert len(info.get('highlights')) == 1
        assert len(info.get('nb_matches')) == 1


class TestGetMatch:
    @pytest.fixture
    def setup(self, mocker):
        def mock_get_info(year, input_str, search_fields, size, verbose, highlights, fuzzy_ok=False) -> dict:
            return {"year": year, "input_str": input_str, "search_fields": search_fields, "size": size,
                    "verbose": verbose, "highlights": highlights, "fuzzy_ok": fuzzy_ok}

        mocker.patch("project.server.main.match_rnsr.get_info", side_effect=mock_get_info)

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_code(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["code_numbers"]
        assert info.get("size") == 20
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_label(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_code_label(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["code_numbers.labels"]
        assert info.get("size") == 10000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers.labels"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_digit(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_code_digit(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["code_numbers.digits"]
        assert info.get("size") == 20
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers.digits"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_code_fuzzy(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_code_fuzzy(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["code_numbers", "code_numbers.digits"]
        assert info.get("size") == 1000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["code_numbers", "code_numbers.digits"]
        assert info.get("fuzzy_ok") is True

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_city(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_city(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["addresses"]
        assert info.get("size") == 5000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["addresses"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_name(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_name(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["names"]
        assert info.get("size") == 200
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["names"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_acronym(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_acronym(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["acronyms"]
        assert info.get("size") == 5000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["acronyms"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_name(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_supervisors_name(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["supervisors_name"]
        assert info.get("size") == 10000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_name"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_id(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_supervisors_id(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["supervisors_id"]
        assert info.get("size") == 2000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_id"]
        assert info.get("fuzzy_ok") is False

    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(42, "test", False), (42, "test", True)])
    def test_get_match_supervisors_acronym(self, setup, param_year, param_string, param_verbose) -> None:
        info = get_match_supervisors_acronym(param_year, param_string, param_verbose)
        assert info.get("year") == param_year
        assert info.get("input_str") == param_string
        assert info.get("search_fields") == ["supervisors_acronym"]
        assert info.get("size") == 2000
        assert info.get("verbose") is param_verbose
        assert info.get("highlights") == ["supervisors_acronym"]
        assert info.get("fuzzy_ok") is False
