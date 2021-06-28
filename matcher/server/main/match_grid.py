from matcher.server.main.Matcher import Matcher
from matcher.server.main.utils import remove_ref_index


DEFAULT_STRATEGIES = [
    ['grid_name', 'grid_acronym', 'grid_city'],
    ['grid_name', 'grid_city'],
    ['grid_acronym', 'grid_city']
]


def match_grid(query: str = '', strategies: list = None, country_code: str = None) -> dict:
    if strategies is None:
        strategies = DEFAULT_STRATEGIES
    matcher = Matcher()
    return matcher.match(query=query, strategies=strategies, year=country_code, pre_treatment_query=remove_ref_index)
