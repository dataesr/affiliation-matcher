import pytest

from matcher.server.main.match_country import get_countries_from_query


@pytest.mark.parametrize('query,expected_country', [
    ('Tour Mirabeau Paris', ['FR']),
    ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', ['FR']),
    ('N\'importe quoi', []),
    ('Sorbonne Université, INSERM, UMRS 1142 LIMICS, Paris, France, APHP.Sorbonne, Fetal Medicine Department, '
     'Armand Trousseau Hospital, Paris, France.', ['FR'])
])
def test_get_address_from_query(query, expected_country) -> None:
    matched_country = get_countries_from_query(query)
    assert matched_country == expected_country
