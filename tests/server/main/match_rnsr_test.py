import pytest
from project.server.main.match_rnsr import match_unstructured, match_fields, get_info, get_match_code


@pytest.mark.skip
class TestMatchUnstructured:
    def test_1(self):
        res = match_unstructured(2015, "INS1640 INSHS Institut des Sciences Humaines et Sociales ORLEANS")
        assert res.get('match') is None

    def test_2(self):
        res = match_unstructured(2015, "MOY1000  Délégation Alsace STRASBOURG")
        assert res.get('match') is None


@pytest.mark.skip
class TestMatchFields:
    def test_3(self):
        res = match_fields(2018, "UMR 5223", "INGENIERIE DES MATERIAUX POLYMERES", "VILLEURBANNE CEDEX", "IMP",
                           "196917744")
        assert res.get('match') == '200711890Y'

    # def test_4(self):
    #    res = match_fields(2019, None, "BUREAU DE RECHERCHES GEOLOGIQUES ET MINIERES", "ORLEANS", "BRGM", "582056149")
    #    assert res.get('match') == '195922846R'


@pytest.mark.skip
class TestGetInfo:
    def test_get_info_by_acronym(self):
        info = get_info(2019, 'PF-CCB', ['acronyms'], 20, False, ['acronyms'], False)
        assert info.get('ids') == ['000021537K']
        assert len(info.get('highlights')) == 1
        assert len(info.get('nb_matches')) == 1


class TestGetMatch:
    @pytest.mark.parametrize("param_year,param_string,param_verbose", [(2019, "PF-CCB", False), (2019, "PF-CCB", True)])
    def test_get_match_code(self, mocker, param_year, param_string, param_verbose):
        def mock_get_info(year, input_str, search_fields, size, verbose, highlights) -> dict:
            return {'year': year, 'input_str': input_str, 'search_fields': search_fields, 'size': size,
                    'verbose': verbose, 'highlights': highlights}

        mocker.patch('project.server.main.match_rnsr.get_info', side_effect=mock_get_info)
        info = get_match_code(param_year, param_string, param_verbose)
        assert info.get('year') == param_year
        assert info.get('input_str') == param_string
        assert info.get('search_fields') == ["code_numbers"]
        assert info.get('size') == 20
        assert info.get('verbose') is param_verbose
        assert info.get('highlights') == ["code_numbers"]
