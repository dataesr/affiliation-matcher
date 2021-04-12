import pytest

from project.server.main.match_country import get_address_from_query


@pytest.mark.parametrize('query,country_iso_3', [
    ('Medical Intensive Care Unit, Hôpital Lyon Sud, Pierre-Bénite 69495, France, COVID-O-HCL Consortium, Hospices '
     'Civils de Lyon, Lyon, France.', 'FR')
])
def test_get_address_from_query(query, country_iso_3) -> None:
    response = get_address_from_query(query)
    assert response.get('match', None) == country_iso_3
