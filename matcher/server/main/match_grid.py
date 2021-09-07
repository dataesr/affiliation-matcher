from matcher.server.main.matcher import Matcher
from matcher.server.main.utils import remove_ref_index


DEFAULT_STRATEGIES = [
    [['grid_name', 'grid_acronym', 'grid_city', 'grid_country'],
     ['grid_name', 'grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_city', 'grid_country'], ['grid_name', 'grid_city', 'grid_country_code'],
     ['grid_acronym', 'grid_city', 'grid_country'], ['grid_acronym', 'grid_city', 'grid_country_code']],
    [['grid_name', 'grid_country'], ['grid_name', 'grid_country_code']],
    [['grid_name', 'grid_city']]
]


def match_grid(conditions: dict) -> dict:
    strategies = conditions.get('strategies')
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(conditions=conditions, strategies=strategies, pre_treatment_query=remove_ref_index)
