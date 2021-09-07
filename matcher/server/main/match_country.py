from matcher.server.main.matcher import Matcher

DEFAULT_STRATEGIES = [
    [['grid_city', 'grid_name', 'grid_acronym', 'country_name']],
    [['grid_city', 'grid_name', 'country_name'], ['grid_city', 'grid_acronym', 'country_name']],
    [['grid_city', 'country_name']],
    [['grid_city', 'grid_name', 'country_subdivision_name', 'country_alpha3']],
    [['grid_city', 'grid_name', 'country_alpha3']],
    [['grid_city', 'grid_acronym', 'country_subdivision_name', 'country_alpha3']],
    [['grid_city', 'country_subdivision_name', 'country_alpha3']],
    [['grid_name', 'grid_city'], ['grid_name', 'country_name']],
    [['grid_acronym', 'country_name']],
    [['country_subdivision_name', 'country_name']],
    [['country_name']],
    [['country_subdivision_name', 'country_alpha3']],
    [['grid_name', 'country_subdivision_name', 'country_subdivision_code']],
    [['grid_name', 'country_subdivision_name']],
    [['grid_name', 'grid_acronym']]
]


def match_country(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(conditions=conditions, strategies=strategies, field='country_alpha2')
