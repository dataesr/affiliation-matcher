from project.server.main.match_rnsr import match_unstructured, match_fields


def test_1():
    res = match_unstructured(2015, "INS1640 INSHS Institut des Sciences Humaines et Sociales ORLEANS")
    assert res.get('match') == None

def test_2():
    res = match_unstructured(2015, "MOY1000  Délégation Alsace STRASBOURG")
    assert res.get('match') == None

def test_3():
    res = match_fields(2018, "UMR 5223", "INGENIERIE DES MATERIAUX POLYMERES", "VILLEURBANNE CEDEX", "IMP", "196917744")
    assert res.get('match') == '200711890Y'

def test_4():
    res = match_fields(2019, None, "BUREAU DE RECHERCHES GEOLOGIQUES ET MINIERES", "ORLEANS", "BRGM", "582056149")
    assert res.get('match') == '195922846R'
