import pytest

from project.server.main.match_country import get_address_from_query


@pytest.mark.parametrize('query,expected_country', [
    ('Tour mirabeau paris', 'fr')
])
def test_get_address_from_query(query, expected_country) -> None:
    matched_country = get_address_from_query(query)
    assert matched_country == expected_country
