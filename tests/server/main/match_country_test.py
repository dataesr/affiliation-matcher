import pytest

from project.server.main.match_country import get_country_from_query


@pytest.mark.parametrize('query,expected_country', [
    ('Tour Mirabeau Paris', 'fr'),
    ('Inserm U1190 European Genomic Institute of Diabetes, CHU Lille, Lille, France', 'fr'),
    ('Inserm U1190 European Genomic Institute of Diabetes CHU Lille Lille France', None),
    ('Sorbonne Université, INSERM, UMRS 1142 LIMICS, Paris, France, APHP.Sorbonne, Fetal Medicine Department, '
     'Armand Trousseau Hospital, Paris, France.', 'fr')
])
def test_get_address_from_query(query, expected_country) -> None:
    matched_country = get_country_from_query(query)
    assert matched_country == expected_country
